# Task 1 – Výber prompting frameworkov pre text-to-SQL

## Cieľ
Pripraviť tri opakovane použiteľné prompty pre generovanie SQLite SELECT dopytov z prirodzeného jazyka v Task 2. Použité frameworky sú ICIO, RTF a CO-STAR. ROSES sa nepoužíva. Každý prompt obsahuje dve rovnaké demonštrácie otázka → SQL, takže nejde o zero-shot prompting.

## ICIO: Instruction, Context, Input, Output
Zdroj: https://frompting.com/frameworks/icio

ICIO bol zvolený pre jasné oddelenie operácie, databázového kontextu, vstupnej otázky a výstupného formátu. Instruction definuje prevod na SQL, Context obsahuje schému a interpretačné pravidlá, Input obsahuje oddelenú otázku a Output vyžaduje iba vykonateľný dopyt. Demonštrácie dopĺňajú framework o few-shot prompting.

Očakávame, že toto rozdelenie podporí správne používanie tabuliek a stĺpcov a pomôže ignorovať nesúvisiace poznámky. Oddelenie vstupu tiež jasne označuje text, ktorý sa má spracovať. Je to hypotéza, nie nameraný výsledok.

## RTF: Role, Task, Format
Zdroj: https://frompting.com/frameworks/rtf

RTF bol zvolený ako jednoduchší spôsob organizácie rovnakej úlohy. Role definuje službu generujúcu SQLite dopyty, Task zahŕňa prevod, schému, pravidlá, demonštrácie a otázku. Format určuje presný typ výstupu bez vysvetlení.

Očakávame, že explicitná rola a formát obmedzia nadbytočný text. Porovnaním overíme, či jednoduchšie členenie postačuje aj pre otázky s rušivými poznámkami. Samotný počet sekcií nepreukazuje kratší prompt ani rýchlejšiu inferenciu; čas bude potrebné zmerať.

## CO-STAR: Context, Objective, Style, Tone, Audience, Response
Zdroj: https://frompting.com/frameworks/co-star

CO-STAR bol zvolený na porovnanie podrobnejšieho členenia s ICIO a RTF. Context obsahuje schému, pravidlá a demonštrácie; Objective určuje prevod otázky; Style žiada konvenčnú SQL syntax; Tone vylučuje konverzačný jazyk; Audience identifikuje automatický vyhodnocovač a Response definuje výstup.

Zdroj orientuje CO-STAR najmä na textové výstupy, kde záleží na štýle a publiku. Pri SQL je preto potrebné jeho prispôsobenie. Očakávame, že explicitný príjemca a formát podporia použiteľnosť výstupu. Zároveň overíme, či dodatočné sekcie prinášajú úžitok alebo iba zväčšujú vstup. Nezaručujeme vyššiu presnosť.

## Spoločné podmienky a demonštrácie
Všetky tri prompty obsahujú rovnakú schému, interpretačné pravidlá, dve demonštrácie a požiadavku vrátiť jediný SELECT bez Markdownu, komentárov alebo výsledkov. Líši sa organizácia podľa frameworku; CO-STAR navyše explicitne vyjadruje jeho vlastné sekcie štýlu, tónu a príjemcu. Experiment preto porovná konkrétne verzie promptov, nie univerzálnu kvalitu frameworkov.

Demonštrácie používajú vymyslené názvy sampleville a exampletown a nepreberajú otázky z hodnoteného datasetu. Ukazujú filtrovanie, prísnu hranicu ratingu, ignorovanie odbočky a výber maximálneho ratingu vrátane zhôd. Ich SQL bolo overené na samostatnej syntetickej databáze. Očakávané výsledky hodnotených otázok nie sú súčasťou promptov.

## Overenie interpretačných predpokladov
Pri vyhľadávaní reštaurácií sa vracia ID a NAME. Pri dvoch neprázdnych otázkach na najlepšiu reštauráciu v konkrétnom meste sa názvy vybraných reštaurácií zhodovali s referenčnými názvami, ale ich ID sa líšili: portola park má v databáze ID 2633 oproti referenčnému 3; catahoula restaurant and saloon má ID 4808 oproti referenčnému 1457. V oboch prípadoch existuje iba jeden zodpovedajúci kandidát, takže tieto kontroly nedokazujú interpretáciu „best“ ani pravidlo zhôd. Maximálny rating a vrátenie všetkých zhôd zostávajú deklarovanými interpretačnými voľbami. Rozdiely v ID môžu znižovať meranú presnosť aj pri správnom SQL a treba ich uviesť v Task 2; prompty ich nesmú obchádzať natvrdo zadanými odpoveďami.

Otázky typu „where can I eat“ sú vyhľadávaním reštaurácií, nie žiadosťou o adresu. Pri otázke na adresu konkrétneho podniku používame HOUSE_NUMBER, STREET_NAME, CITY_NAME. Záverečných päť otázok na umiestnenie konkrétneho podniku má prázdne očakávané výsledky, a preto z nich nemožno potvrdiť poradie ani počet adresných stĺpcov. Adresný formát zostáva predpokladom, ktorý treba uviesť aj pri interpretácii Task 2.

Schéma je v promptoch uvedená so stĺpcami a SQLite typmi; deklarácie kľúčov nahrádzajú explicitné pravidlá pre spojenie tabuliek. Ide o zjednodušený opis existujúcej databázy, nie pokyn na jej vytvorenie. Pri kontrole databázy neboli nájdené opakované ID reštaurácií.

## Odovzdávané súbory a použitie
- prompts.json: všetky tri šablóny s identifikátormi, zdrojmi a metadátami.
- icio_v1.txt, rtf_v1.txt, co_star_v1.txt: samostatné čitateľné verzie tých istých promptov.
- report_sk.md: tento report.

Zástupný symbol {{question}} sa pri generovaní nahradí aktuálnou otázkou. Dataset ani referenčné výsledky sa nevkladajú do šablóny ako odpovede. Pri porovnaní treba zachovať model, nastavenia a otázky a začať novú session pre každý prompt. Predikcie, časy inferencie, metriky a vizualizácie patria do Task 2 a zatiaľ neboli vytvorené.

## Technická poznámka k Task 2
Poskytnutý validátor nepreskakuje hlavičku CSV schémy. Navyše pri chybnom SQL ukončí celé hodnotenie. Pred experimentom treba pripraviť zdokumentovanú opravu alebo adaptér so zachovaním pôvodných dát a spôsobu porovnávania výsledkov. Treba tiež preveriť zistené rozdiely medzi referenčnými ID a databázou. Pôvodný validátor ani dáta neboli upravené.
