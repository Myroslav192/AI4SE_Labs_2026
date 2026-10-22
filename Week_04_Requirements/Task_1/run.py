"""Command-line entry point. Python 3.10+; no input filenames are hard-coded."""
import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from refinement.corpus import chunk_documents, load_corpus
from refinement.llm import AgentClient, write_json
from refinement.pipeline import ALLOWED_MODELS, Config, Network
from refinement.schemas import CheckResult


def model_options(parser):
    parser.add_argument("--extractor-model", default="gpt-4o-mini", choices=sorted(ALLOWED_MODELS))
    parser.add_argument("--editor-model", default="gpt-5-mini", choices=sorted(ALLOWED_MODELS))
    parser.add_argument("--reviewer-model", default="gpt-5-nano", choices=sorted(ALLOWED_MODELS))
    parser.add_argument("--api-mode", choices=["responses", "chat"], default="responses")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Source-grounded LangGraph requirements refinement")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Read and inventory the corpus without calling any API")
    inspect.add_argument("--input", type=Path, required=True)
    inspect.add_argument("--output", type=Path, default=Path("artifacts/inspection"))
    inspect.add_argument("--chunk-chars", type=int, default=12000)
    run = sub.add_parser("run", help="Execute the actual three-model LangGraph network")
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--output", type=Path, default=Path("artifacts/run"))
    run.add_argument("--max-revisions", type=int, default=2)
    run.add_argument("--chunk-chars", type=int, default=12000)
    run.add_argument("--language", default="English")
    run.add_argument("--max-calls", type=int, default=150)
    run.add_argument("--review-workers", type=int, default=4)
    run.add_argument("--rescan-sources", action="store_true", help="Repeat full-document audits after every revision")
    run.add_argument("--feedback", type=Path, help="Optional source-grounded review feedback JSON")
    run.add_argument("--source-audit-rounds", type=int, help="Optional cap on full-source rounds when rescanning")
    model_options(run)
    check = sub.add_parser("check-api", help="Make one tiny Structured Outputs request per model")
    check.add_argument("--output", type=Path, default=Path("artifacts/api_check"))
    model_options(check)
    graph = sub.add_parser("graph", help="Save a Mermaid diagram of the compiled LangGraph without API calls")
    graph.add_argument("--output", type=Path, default=Path("graph.mmd"))
    args = parser.parse_args(argv)
    # Always find .env beside this script, independent of the caller's directory.
    load_dotenv(Path(__file__).resolve().with_name(".env"), override=False)
    client = None
    try:
        if args.command == "inspect":
            documents, skipped = load_corpus(args.input)
            chunks = chunk_documents(documents, args.chunk_chars)
            data = dict(document_count=len(documents), chunk_count=len(chunks), skipped_files=skipped,
                        documents=[dict(id=doc.id, path=doc.path, characters=len(doc.text), sha256=doc.sha256,
                                        lines=len(doc.text.splitlines())) for doc in documents])
            write_json(args.output / "corpus_inventory.json", data)
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 2 if skipped else 0
        if args.command == "graph":
            compiled = Network(Config(Path("data"), Path("artifacts")), None).build()
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(compiled.get_graph().draw_mermaid(), encoding="utf-8")
            print(f"Graph saved to {args.output.resolve()}")
            return 0
        config = Config(input_dir=args.input if args.command == "run" else Path("data"),
                        output_dir=args.output, extractor_model=args.extractor_model,
                        editor_model=args.editor_model, reviewer_model=args.reviewer_model,
                        language=getattr(args, "language", "English"),
                        max_revisions=getattr(args, "max_revisions", 2),
                        chunk_chars=getattr(args, "chunk_chars", 12000),
                        review_workers=getattr(args, "review_workers", 4),
                        rescan_sources=getattr(args, "rescan_sources", False),
                        review_feedback=getattr(args, "feedback", None),
                        source_audit_rounds=getattr(args, "source_audit_rounds", None))
        config.validate()
        client = AgentClient(args.output, max_calls=getattr(args, "max_calls", 3), api_mode=args.api_mode)
        if args.command == "check-api":
            for model in (config.extractor_model, config.editor_model, config.reviewer_model):
                client.invoke("connectivity_check", model, "Return ok=true in the requested schema.", {}, CheckResult, 1000)
            print("All three models accepted Structured Outputs requests.")
            return 0
        compiled = Network(config, client).build()
        (args.output / "graph.mmd").write_text(compiled.get_graph().draw_mermaid(), encoding="utf-8")
        result = compiled.invoke({}, config={"recursion_limit": 20 + 6 * config.max_revisions})
        print(f"Requirements saved to {result['result_path']}")
        return 0 if result["review_passed"] else 2
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
