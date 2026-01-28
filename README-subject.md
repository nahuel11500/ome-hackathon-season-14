# Team: Les puissants gardes forestiers

# Start of Season 14 Hackathon - Data For Good x L’Observatoire des Médias sur l’Écologie
As climate and environmental crises intensify at an unprecedented rate, media coverage of these issues is becoming a key lever for informing, raising awareness and mobilising society as a whole. 

However, media coverage of these issues remains largely insufficient, both in terms of volume and quality. According to the latest data from the International Media and Climate Change Observatory, global coverage of environmental issues has been in steady decline since 2022.

The Media Observatory on Ecology (OME) aims to objectively assess this phenomenon in France. In 2026, the methodology was improved, enabling more accurate detection of news reports. A second stage of analysis aims to identify, for certain target themes (agriculture/food and mobility), the angle of media coverage: impact on health, purchasing power, daily life, etc.
## How to use this repo
This repository is your starting point for the hackathon. Run the different services using 
```bash
docker compose up --build inference
````
The `--build` flag is optional in case you have updated the code in order to rebuild the dockerfile.

There are 4 services in the `docker-compose.yml` the most important ones are `inference`, `postgres` and `metabase`. With regards to training models, a little example script is present but feel free to train models on a Google collab environment or on your machine if the training is more optimised (for example when using Apple Silicon). The important service you will be judged on is the `inference` but feel free to store results in the postgres database that has been setup, and to use metabase for data visualisations. 

Metabase and data visualisations can help illustrate the value your analysis brings to the solution, or to produce a demo environment, but ultimately you will be judged on the inference solution.

Remember the judging criteria:
* Depth of analysis
* Level of technical maturity
* Frugality
* Use of FOSS tools and models

# Tasks

You are not required to complete these tasks sequentially, you can pick and choose whatever part of the hackathon you find the most interesting and work on that.

## Task 1: Classification and identification of news reports in the texts. 

The texts, retrieved using the new methodology currently being developed at the OMÉ, are quickly annotated with an LLM in two categories: “report” and “segment”. 

The “report” category includes all texts considered to contain a complete report, while the “segment” category includes all texts considered to be a mixture of several segments from different reports/studio debates, etc.

The aim of the exercise is twofold. On the one hand, to replicate the results of the LLM, even if imperfect, with fewer computing resources. On the other hand, it is to provide a more open solution for analysing the semantic structure of the texts and how they differ from one another, and how the different parts of the text differ from one another. For this first step, be sure to analyse the different parts of the text by projecting them onto an embedding space.


## Task 2: Classification of categories 

As in step one, there is a more trivial classification into four categories (Agriculture and food, Mobility and transport, Energy and other). There is also, and this is much more interesting, an open question about the content of the texts according to the categories.

The ultimate goal is to provide complete or partial answers to the questions asked in the ‘Examples of identifiable frameworks’. The advice here is not to get stuck in a crude approach using only gen ia, but to try to find simple solutions (even keyword approaches) that give good results. That's the winning formula!

# Evaluation

This competition values creative solutions based on frugality. The questions are deliberately open-ended, allowing you to find solutions we have never considered. There is no single correct answer; the aim is to find solutions to a real problem we are facing! 

Selection criteria:

* Comprehensiveness of the approach: how well the solution meets the needs.
* Technical frugality.
* Level of openness of the models used: consider the difference between open weights, open code and open source. If possible, avoid models from Big Tech.
* Level of maturity and industrialisation: rather than just providing a notebook with more or less interesting results, consider using Docker to create a containerised solution with multiple services (there is an example in the repo).


NB: There will be no computing power available for the hackathon, so make sure you find a solution that can run on a local computer. You can also use Google Colab notebooks during the development phase, but the solution should be independent and run on a computer using Docker. Bear in mind that a slightly less powerful but much more frugal solution will be greatly appreciated. 
