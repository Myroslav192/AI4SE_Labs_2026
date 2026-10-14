# Task 3 a Task 4 – pripravená metodika

Stav: implementácia a metodika sú pripravené. Hodnoty pre ICIO, RTF a CO-STAR ešte neboli vypočítané, pretože súbory predikcií zatiaľ nie sú dostupné v tomto pracovnom prostredí. Tento dokument je podklad pre finálne reporty, nie hotové vyhodnotenie.

## Task 3: Balanced Row F1

Pôvodná execution accuracy pridelí otázke 1 len vtedy, keď je celý výsledok SQL rovnaký ako referencia, inak 0. Nerozlišuje takmer správny výber od úplne nesprávneho. Navrhujeme doplnkovú metriku Balanced Row F1 (BRF1): vyvážený priemer prekrytia výsledných riadkov, osobitne pre otázky s prázdnou a neprázdnou referenciou.

Pre otázku i označme E_i multiset referenčných riadkov a P_i multiset predikovaných riadkov. Multiset zachováva počet výskytov rovnakých riadkov. Platí:

F1_i = 2 × |E_i ∩ P_i| / (|E_i| + |P_i|).

Prienik počíta minimálny počet výskytov každého rovnakého riadka. Poradie riadkov neovplyvňuje skóre; poradie stĺpcov, ID, názvy aj duplicity zostávajú významné, rovnako ako v pôvodnom validátore.

- Ak oba výsledky sú prázdne a SQL sa vykonalo úspešne, F1_i = 1.
- Ak je prázdny iba jeden výsledok, F1_i = 0.
- Chybný, chýbajúci alebo časovo prekročený SQL dopyt dostáva 0, aj keď je referencia prázdna.

BRF1 = 0,5 × priemer F1_i pre prázdne referencie + 0,5 × priemer F1_i pre neprázdne referencie.

Ak niektorá skupina chýba, BRF1 je nedostupné (null), nie nahradené inou metrikou. V poskytnutom datasete sú obe skupiny: 43 prázdnych a 112 neprázdnych referencií. Implementácia však tieto počty nemá zadané natvrdo, odvodzuje ich z dát.

### Prečo je metrika vhodná

F1 penalizuje chýbajúce aj nadbytočné riadky. Otázka s dvoma správnymi riadkami z troch a bez nadbytočných riadkov dostane 0,8 namiesto úplnej nuly. Priemerovanie na úrovni otázok bráni tomu, aby otázka s tisíckou riadkov dominovala otázke s jedným riadkom.

Vyváženie skupín oddeľuje schopnosť správne vrátiť prázdny výsledok od schopnosti nájsť skutočné zhody. Systém, ktorý vždy úspešne vráti prázdny výsledok, má pri existencii oboch skupín BRF1 = 0,5; zároveň má F1 neprázdnej skupiny 0. Preto vždy uvádzame obe zložky aj pôvodnú accuracy a neinterpretujeme samotné číslo 0,5 ako dôkaz dobrej kvality.

Prínos návrhu spočíva v kombinácii bežného multisetového F1 a vyváženia skupín podľa prázdnosti referencie pre tento konkrétny problém. Netvrdíme, že F1 alebo vyvážené priemerovanie sú nové vedecké metódy.

BRF1 pôvodnú metriku dopĺňa, nenahrádza. Presná správnosť celého SQL výsledku zostáva dôležitá. Žiadna z metrík nedokazuje ekvivalenciu SQL na všetkých možných databázach.

### Obmedzenie poskytnutých referencií

V dvoch skorších kontrolách sa ID v referenciách líšili od ID v databáze pri rovnakých názvoch reštaurácií. BRF1 úmyselne nemení ID ani neporovnáva iba názvy: taká zmena by definovala iný cieľ. Tieto nezrovnalosti preto môžu znížiť aj BRF1. Vo finálnom reporte treba odlíšiť chyby modelu od chýb alebo nekompatibility podkladov.

## Použitie implementácie

metrics.py prijíma JSON so skutočnými výsledkami vykonania SQL, nie priamo CSV predikcií. Vyhodnocovací krok Task 2 musí ku každej otázke zachovať referenčné a predikované riadky. Chýbajúce predikcie sa nesmú vynechať.

Príklad formátu pre samostatnú syntetickú ukážku:

```json
[
  {"question_id": 1, "expected_rows": [[1, "A"], [2, "B"]], "predicted_rows": [[1, "A"]]},
  {"question_id": 2, "expected_rows": [], "predicted_rows": []},
  {"question_id": 3, "expected_rows": [], "predicted_rows": null, "error": "SQL execution failed"}
]
```

```text
python metrics.py executed_icio.json --output scores_icio.json
python metrics.py executed_rtf.json --output scores_rtf.json
python metrics.py executed_co_star.json --output scores_co_star.json
python paired_statistics.py --scores ICIO=scores_icio.json RTF=scores_rtf.json CO-STAR=scores_co_star.json --output statistics.json
```

Stačí štandardná knižnica Pythonu. Príklady vyššie nie sú výsledkami skutočných experimentov.

## Task 4: plán štatistického porovnania

Jednotkou porovnania je rovnaká otázka zodpovedaná tromi promptmi. Vektory preto musia byť spárované podľa question_id. Kód odmietne nezhodné množiny ID, duplicitné ID a nesúlad referenčných skupín.

1. Pre execution accuracy použijeme obojstranný exaktný McNemarov test. Porovnáva počet otázok správnych iba pre A s počtom otázok správnych iba pre B. Ak sa nenachádza žiadny nesúhlasný pár, p = 1.
2. Pre BRF1 použijeme obojstranný párový permutačný test. V rámci každej otázky náhodne vymieňa skóre promptov A a B, čím sa zachovajú páry aj referenčné skupiny. Testuje sa rozdiel BRF1, nie obyčajný nevyvážený priemer.
3. Najviac 16 nenulových rozdielov umožní úplný výpočet všetkých znamienkových permutácií. Pri väčšom počte použijeme 19 999 náhodných permutácií a korekciu (počet extrémnych + 1)/(počet pokusov + 1). Seed je 20261014.
4. Tri dvojice promptov a dve metriky vytvoria šesť testov. Na celú túto rodinu použijeme Holmovu korekciu a hranicu alfa = 0,05. Report uvedie pôvodné aj upravené p-hodnoty.
5. Uvedieme rozdiely A − B a opisné 95 % percentilové bootstrap intervaly z 10 000 opakovaní. Otázky sa vzorkujú v pároch; pre BRF1 osobitne v oboch referenčných skupinách. Intervaly nie sú simultánne korigované; rozhodnutie o významnosti vychádza z upravených p-hodnôt.

### Predpoklady a rozsah záverov

Permutačný test predpokladá zameniteľnosť označení promptov v rámci otázky za nulovej hypotézy. Štatistické testy aj bootstrap pracujú s otázkami ako jednotkami; podobné šablóny otázok môžu vytvárať závislosti. Ak je možné vopred a nezávisle od výsledkov určiť skupiny podobných otázok, je vhodná doplnková analýza na úrovni skupín. Bez nej budeme výsledky označovať za exploratívne.

Jeden beh na prompt neumožňuje odhadnúť variabilitu medzi opakovanými behmi agenta. Významný rozdiel medzi otázkami preto nie je dôkaz, že sa rovnaký rozdiel zopakuje v každom novom behu. Nevýznamnosť zase nie je dôkaz ekvivalencie.

Pre čas máme iba jedno pozorovanie na prompt, takže nevykonáme test významnosti časov. Uvedieme len namerané trvania a pomery. End-to-end čas zahŕňa nástroje, súborové operácie a prípadné čakanie na súhlasy; nie je čistým časom inferencie.

## Plán tabuliek, grafov a interpretácie

- Súhrnná tabuľka: prompt, model, reasoning, počet otázok, accuracy, BRF1, obe zložky F1, chyby vykonania a čas agenta.
- Graf accuracy a BRF1 pre tri prompty, doplnený zobrazením prázdnej a neprázdnej skupiny.
- Samostatný graf nameraných časov s jednoznačným označením typu merania.
- Tabuľka párových rozdielov, intervalov a upravených p-hodnôt; prípadne graf intervalov rozdielov.
- Ukážky zhodných aj odlišných chýb zo skutočných predikcií, najmä pri JOIN, maximálnom ratingu, podmienkach a rušivých vsuvkách.

Vysvetlenia rozdielov budú rozlišovať pozorovanie a hypotézu. Zohľadníme obsah promptov, rovnaké nastavenie GPT-6.1 Sol / Medium, kontext počas dávkového spracovania, správanie agenta pri čítaní a zápise a problémy referencií. Nepripíšeme rozdiely automaticky názvu frameworku.

## Zdroje štatistických metód

- McNemarov exaktný test: https://www.statsmodels.org/dev/generated/statsmodels.stats.contingency_tables.mcnemar.html
- Párové permutácie: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html
- Párový bootstrap a percentilové intervaly: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
- Holmove úpravy p-hodnôt: https://github.com/statsmodels/statsmodels/blob/main/statsmodels/stats/multitest.py

Kód používa vlastnú implementáciu týchto výpočtov so štandardnou knižnicou, nie volania SciPy alebo statsmodels. Overených bolo 12 syntetických testov: čiastočný prekryv, duplicity, poradie stĺpcov, odlišné ID, prázdne výsledky, zlyhania vykonania, vyváženie skupín, chýbajúca skupina, duplicitné ID, známa p-hodnota, Holmove úpravy, permutácie, bootstrap a zarovnanie párov. Syntetické testy nenahrádzajú vyhodnotenie reálnych predikcií.
