# Kiesraad EML Data 

Onderstaand is een kort overzicht van mijn proces in het gebruiken van EML data en het maken van een gestructureerde dataset voor een specifieke vraagstelling. 


## vraagstelling

Van Henk van der Kolk kreeg ik de vraag of ik een dataset met resultaten per kandidaat kon maken, om de verkiesbaarheid kandidaten op individueel niveau in kaart te kunnen brengen. (Ik kan me de exacte onderzoeksvraag niet meer herinneren, deze is ook niet direct relevant.)

Voor dit onderzoek zijn nodig...

- Kandidaten (woonplaats, gender, etc.)
- Uitslagen per verkiezing en domein
- Uitslagen per kandidaat en kiesdistrict (waar een verkiezingsdomein uit meerdere kiesdistricten bestaat).

Om mogelijke verbanden tussen woonplaats, over tijd, etc. te kunnen onderzoeken, is het nodig dat we de volgende koppelingen kunnen maken;

- kandidaat aan uitslag (verkozen of niet) 
- kandidaat aan aantal stemmen per kiesdistrict
- kandidaat over tijd.

## gebruikte data

Praktisch betekend dit het koppelen van kandidaten per kiesdistrict/waterschap (`xxx/KandidatenLijsten_xxx`), aantal stemmen per kandidaat/district (`TotaalTelling_xxx`), en gekozen kandidaten (`Resultaat_xxx`). 

We doen dit voor de provinciale en waterschaps verkiezingen van 2015, 2019, en 2023. Voor elke set verkiezingen (e.g., alle provinciale verkiezingen in 2023) verzamel ik eerst alle data uit de individuele eml/xml bestanden (e.g., alle kandidaten over alle provincies en kieslijsten), en sla deze als een csv. Hierbij voeg ik ook alle aanwezige metadata toe, e.g., Election, Contest, Affiliation, etc.. Dit doe ik ook voor de totaaltelling en resultaten, en als laatste koppel ik kandidaten, stemmen, en resultaten. 

Dit betekend dat ik alle data eerst moet standaardiseren, maar maakt de uiteindelijke koppeling makkelijker. Een alternatieve aanpak waar ik per provincie/waterschap/kiesdistrict de data koppel en pas later aggregeer zou het wellicht makkelijker maken om sommige van onderstaande problemen te vermijden, maar maakt onderhoudt en koppeling moeilijker. 

## problemen

In willekeurige volgorde volgt hieronder een overzicht van een aantal van de problemen/vragen waar ik tegenaan liep.

- `ContestName` is in de AB2023 en PS2023 data niet genoemd als het kiesdistrict hetzelfde is als het verkiezingsdomein (i.e., voor alle waterschappen en provincies met één kiesdistrict). In vorige verkiezingen was ContestName altijd gedefinieerd. 
- in `TotaalTelling_xxx` zijn de 'reporting units' verschillend voor verkiezingen met één kiesdistrict (units zijn gemeentes) en meerdere districten (units zijn kiesdistricten). 
- ook in de totaaltellingen, is `ContestIdentifier` ambigu (wat is de contest voor een verkiezing met meerdere districten?), en vooral de gebruikte identifier voor uitslagen met één kieskring lijkt arbitrair ("geen" in 2023, "1" (RegionNumber voor de Kieskring?) in 2019 en 2015). Daarbovenop zijn voor AB2015 specifiek de RegioNumber van een kieskring hetzelfde als die voor het waterschap, en hebben alle totaaltellingen dus een specifieke ContestIdentifier.
- omdat uitslagen in de totaaltelling per 'reporting unit' zijn, en niet per contest, is er geen directe link tussen kandidaatslijsten (per contest) en de geaggregeerde uitslagen. In sommige gevallen beschrijft een reporting unit een contest, maar in andere gevallen niet. (Ik heb de individuele `Telling_xxx` bestanden niet gebruikt, maar na een korte inspectie lijk het er op dat de ContestIdentifier hier wel consistent is.)
- `CandidateIdentifier`s voor kandidaten zijn simpelweg hun positie op de lijst. Dit lijkt logisch, maar zorgt voor problemen in verkiezingen met meerdere kieskringen waar partijen in verschillende kieskringen verschillende kandidatenlijsten aanleveren. In deze gevallen lijkt er meestal een `CandidateShortcode` beschikbaar, maar deze is weer niet beschikbaar voor verkiezingen waar de `CandidateIdentifier` niet ambigu is. Het resultaat is een ingewikkelde conditionele constructie om kandidaten te kunnen koppelen of (zoals ik gedaan heb) het koppelen van kandidaten op basis van naam. Het koppelen van kandidaten in opeenvolgende verkiezingen is momenteel ook alleen mogelijk op naam. 

## Conclusie

Hoewel (bijna) alle data die wij nodig hebben aanwezig is, is het moeilijk om deze op een consistente, efficiente manier te gebruiken. Door inconsistenties in de gebruikte Identifiers en 'reporting units' is het verwerken van de data een tijdsrovend proces en foutgevoelig proces. 

Het gebruik van consistente Identifiers en units over typen verkiezingen, verschillende provincies en - voor zover mogelijk - in verschillende jaren zou het gebruik van deze data veel toegangelijker maken, en de ruimte voor fouten minimaliseren. 

Specifiek voor CandidateIdentifiers vind ik het heel apart dat de identifier niet consistent is. Het zou ideaal zijn als elke kandidaat een persoonlijke unieke identifier krijgt, die onafhankelijk van zijn/haar positie op de kieslijst is, en ook in opeenvolgende verkiezingen hetzelfde blijft. In ieder geval zou ik verwachten dat een CandidateIdentifier binnen één verkiezing niet veranderd tussen de kandidatenlijsten en de resultaten. 