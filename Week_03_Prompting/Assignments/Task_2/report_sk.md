# Task 2 – Porovnanie generovania SQL

## Metóda
Tri samostatné nové chaty Codex vo VS Code použili GPT-6.1 Sol s reasoning Medium. Každý aplikoval jednu šablónu z Task 1 na všetkých 155 pôvodných otázok. Otázky neboli čistené ani skracované; rušivé vsuvky zostali zachované. V generačnom priečinku boli iba otázky a prompty so schémou, bez referenčných výsledkov a obsahu databázy. Inštrukcie zakazovali čítať výstupy predošlých experimentov. Dodané šablóny sa presne zhodujú s Task 1.

Zdrojové predikcie s metadátami sú v predictions/predictions_*.csv, pôvodné časové záznamy v timings/. Model a nastavenia sú evidované v týchto súboroch a používateľskom rozhraní; priebeh generovania nebol nezávisle auditovaný z kompletných chatových logov. Každý súbor má overených 155 unikátnych ID, správne poradie a nezmenené otázky.

## Validácia
Použitý bol skript vyučujúceho. Jeho pôvodná verzia je zachovaná v inputs/evaluate_retrieval_predictions.py. Kópia evaluate_teacher_patched.py preskakuje hlavičku schémy, smeruje na priložené vstupy a prijíma cestu predikcií cez argument. SQL databáza, hodnoty, kľúče ani referenčné odpovede neboli zmenené. Neodstraňovali sa duplicity. Do validačného CLI vstupujú odvodené dvojstĺpcové CSV question,predicted_sql.

evaluate_all.py navyše zaznamenáva výsledok každého dopytu, vykonáva ho na čerstvej kópii databázy iba na čítanie, s päťsekundovým limitom pri SQLite výpočte, a zachováva multisetové porovnávanie. Všetkých 465 SQL sa vykonalo bez chyby. Výsledky adaptéra sa zhodujú s tromi samostatnými behmi minimálne opravenej verzie skriptu vyučujúceho; ich výstupy sú v results/teacher_validation_*.txt.

## Výsledky
| Prompt | Correct / total | Accuracy | SQL errors | Agent time (s) |
|---|---:|---:|---:|---:|
| ICIO | 43/155 | 27.74% | 0 | 320.252 |
| RTF | 43/155 | 27.74% | 0 | 264.463 |
| CO-STAR | 43/155 | 27.74% | 0 | 176.218 |

![Presnosť](figures/accuracy.png)

![Čas agenta](figures/agent_time.png)

Vo všetkých behoch bolo správnych 43/43 otázok s prázdnou referenciou a 0/112 s neprázdnou referenciou. Párová kontrola ukázala, že všetkých 155 SQL textov je úplne rovnakých vo všetkých troch súboroch. Rovnaké sú aj ich výsledky vykonania. Toto je zistenie zo súborov, nie dôkaz, že agent súbory kopíroval; bez plných logov sa pôvod tejto zhody nedá overiť.

## Zistený problém referencií
V 112/112 neprázdnych referenčných odpovediach sa nachádza aspoň jedna dvojica ID–názov, ktorá neexistuje v tabuľke RESTAURANT. Z celkových 13 235 referenčných dvojíc sa ich 13 232 v tabuľke nenachádza. Preto pri bežnom výbere pôvodných ID a názvov z tejto tabuľky nemožno presne reprodukovať tieto referencie. Toto je silná indikácia nesúladu dát a referencií, nie dôkaz konkrétnej príčiny ich vzniku.

Napríklad portola park má v dodanej databáze ID 2633, v referencii 3; catahoula restaurant and saloon má databázové ID 4808, referenčné 1457. Vygenerované SQL pre tieto otázky vyberajú maximálny rating v správnom meste a kuchyni a vracajú správne názvy, no získavajú databázové ID. Referencie preto nedovolia uznať presnú zhodu. Nesúlad sa nesmie riešiť hard-code odpoveďami alebo tichým premapovaním ID.

Prázdne zhody tiež samy osebe nedokazujú správnosť zámeru SQL: aj nesprávny filter môže vrátiť prázdny výsledok. Namerných 27,74 % nemožno interpretovať ako čistý odhad schopností modelu.

## Čas a obmedzenia
Časy pochádzajú zo skutočných UTC štartových a koncových značiek; ich rozdiely boli overené. Ide o end-to-end čas agenta vrátane nástrojov a súborových operácií, prípadne čakania na povolenia. Čistý inference time ani časy jednotlivých otázok nie sú z tohto rozhrania k dispozícii. Požiadavka na meranie čistého času inferencie preto nie je plne pokrytá; report tento nedostatok explicitne uvádza namiesto vymyslených hodnôt.

V tomto jednom pozorovaní bol CO-STAR najrýchlejší. Z jedného behu na prompt a pri rovnakých SQL nemožno vyvodiť všeobecnú rýchlostnú výhodu frameworku. Všetky prompty používali rovnaké pravidlá a demonštrácie, preto je rovnaký výsledok možný. Formát dávkového spracovania a systémové inštrukcie agenta sú ďalšie faktory.

## Reprodukcia
Spustite `python evaluate_all.py` v ľubovoľnom priečinku; cesty sa riešia podľa umiestnenia skriptu. Potrebná je iba štandardná knižnica Pythonu. Obrázky sú priložené aj vo formáte SVG. Generovanie predikcií bolo vykonané agentom; vyhodnocovací kód predikcie nevytvára ani neopravuje. Pre plnú reprodukciu generovania treba znovu použiť uložené šablóny v nezávislých chatoch s rovnakými nastaveniami; výsledok sa nemusí presne zopakovať.
