
# IMRRF
Codes for NAACL 2025 Paper [IMRRF: Integrating Multi-Source Retrieval and Redundancy Filtering for LLM-based Fake News Detection](https://aclanthology.org/2025.naacl-long.461/)
# Introduction
The widespread use of social networks has significantly accelerated the dissemination of information but has also facilitated the rapid spread of fake news, leading to various negative consequences. Recently, with the emergence of large language models (LLMs), researchers have focused on leveraging LLMs for automated fake news detection. Unfortunately, many issues remain to be addressed. First, the evidence retrieved to verify given fake news is often insufficient, limiting the performance of LLMs when reasoning directly from this evidence. Additionally, the retrieved evidence frequently contains substantial redundant information, which can interfere with the LLMs’ judgment. To address these limitations, we propose a Multiple Knowledge Sources Retrieval and LLM Knowledge Conversion framework, which enriches the evidence available for claim verification. We also introduce a Redundant Information Filtering Strategy, which minimizes the influence of irrelevant information on the LLM reasoning process. Extensive experiments conducted on two challenging fact-checking datasets demonstrate that our proposed method outperforms state-of-the-art fact-checking baselines.
![IMRRF框架图](./framework.png)
First, install all the required packages:
```bash
pip install -r requirements.txt
```
# Dataset Preparation
We refer to the steps in paper [Fact-Checking Complex Claims with Program-Guided Reasoning](https://github.com/teacherpeterpan/ProgramFC/tree/main) to prepare the dataset and specific corpus.
# Specific Corpus Retrieval
```bash
python corpus_retrieve.py
```
# Key Entity Based Knowledge Graph Retrieval
Run the following command to retrieve relevant paths from the wikidata knowledge graph:
```bash
python KG_search.py
```
Then run the following command to convert the path results into natural language for the model to understand:
```bash
python process_KG.py
```
# Redundant Information Filtering
Run the following command to filter redundant information from the retrieved external evidence:
```bash
python generate_summary.py
```
# LLM World Knowledge Conversion
Run the following command to have LLMS convert internal knowledge into additional supplementary evidence:
```bash
python generate_evidence.py
```
# Claim Verification
```bash
python execute.py
```
# Reference
Please cite the paper in the following format if you use this dataset during your research.
```bash
@inproceedings{li-etal-2025-imrrf,
    title = "{IMRRF}: Integrating Multi-Source Retrieval and Redundancy Filtering for {LLM}-based Fake News Detection",
    author = "Li, Dayang  and Li, Fanxiao  and Song, Bingbing  and Tang, Li  and Zhou, Wei",
    editor = "Chiruzzo, Luis  and Ritter, Alan  and Wang, Lu",
    booktitle = "Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)",
    year = "2025",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.naacl-long.461/",
    doi = "10.18653/v1/2025.naacl-long.461",
    pages = "9127--9142",
    ISBN = "979-8-89176-189-6",
}
```
# Q&A
if you encounter any problem, please leave an issue in the github repo.
