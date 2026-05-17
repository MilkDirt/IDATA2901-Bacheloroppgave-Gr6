# Rapport — del 1: teori

## Innledning

Denne delen av rapporten beskriver det teoretiske grunnlaget for bachelorprosjektet. Prosjektet undersøker hvordan kunstig intelligens kan brukes til å effektivisere arbeid med byggesøknader og bygningsvisualisering. Teorien danner grunnlaget for valg av arkitektur, teknologier og arbeidsmetoder i løsningen.

## Kunstig intelligens i byggesaksbehandling

Byggesaksbehandling innebærer ofte arbeid med store mengder dokumentasjon, lover, forskrifter og tekniske beskrivelser. Dette gjør fagområdet godt egnet for digitale verktøy som kan støtte innhenting, strukturering og analyse av informasjon. Kunstig intelligens kan bidra med å hente ut relevant informasjon fra dokumenter, oppsummere innhold og gi brukeren raskere tilgang til beslutningsgrunnlag.

I dette prosjektet er målet ikke å erstatte fagpersoner, men å støtte dem i arbeidsprosessen. Løsningen skal derfor fungere som et hjelpemiddel som gjør det enklere å finne relevant informasjon og visualisere forslag raskt.

## Store språkmodeller

Store språkmodeller (LLM-er) er modeller som er trent på store mengder tekst og kan brukes til å generere, oppsummere og tolke språk. Slike modeller er spesielt nyttige i systemer der brukeren stiller spørsmål med naturlig språk. En språkmodell alene har imidlertid begrensninger, fordi den ikke nødvendigvis kjenner til prosjektspesifikke dokumenter eller oppdatert informasjon.

For å gjøre modellen mer pålitelig i praksis, må den kombineres med mekanismer som gir tilgang til relevante datakilder. Dette er bakgrunnen for at prosjektet benytter en RAG-basert løsning.

## Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation er en metode der en språkmodell kombineres med dokumenthenting. Først henter systemet ut relevante tekstutdrag fra en samling dokumenter. Deretter brukes disse utdragene som kontekst når språkmodellen genererer et svar. På denne måten kan svarene i større grad forankres i faktiske kilder.

RAG er relevant i dette prosjektet fordi brukeren skal kunne stille spørsmål om dokumenter som planer, bestemmelser og byggesøknader. Ved å hente relevante utdrag før svaret genereres, kan systemet gi mer presise og etterprøvbare svar enn en språkmodell alene.

## Embeddings og vektorsøk

For å finne relevante dokumentutdrag må tekst representeres på en måte som kan sammenlignes matematisk. Dette gjøres ved hjelp av embeddings, som er numeriske representasjoner av tekst. Tekst med lignende innhold vil da få lignende representasjoner i et vektorrom.

Når dokumentene er gjort om til embeddings, kan de lagres i en vektorindeks. Ved et spørsmål fra brukeren genereres en embedding av spørsmålet, og systemet søker etter tekstutdrag med høyest semantisk likhet. Denne metoden er sentral i moderne spørsmåls- og svarsystemer som arbeider med store dokumentmengder.

## Visualisering og generativ modellering

Den andre delen av prosjektet handler om å generere og plassere bygningsgeometri i Rhino. Her brukes kunstig intelligens til å tolke tekstbeskrivelser og omsette dem til parametere som kan styre genereringen av bygningselementer. Dette knytter språklige beskrivelser til visuell og geometrisk modellering.

I en slik kontekst fungerer AI som et bindeledd mellom brukerens intensjon og det tekniske modelleringsarbeidet. Dette kan bidra til raskere iterasjon, mer intuitive arbeidsprosesser og bedre støtte i tidlige designfaser.

## Oppsummering

Teorien viser at prosjektet bygger på en kombinasjon av språkmodeller, dokumenthenting og semantisk søk. Samtidig kobles dette mot generativ modellering i Rhino for å støtte visualisering av bygg. Videre i rapporten kan denne teorien brukes som grunnlag for metodevalg, systemdesign og diskusjon av resultatene.
