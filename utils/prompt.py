EXTRACT_ENTITIES = """Instruction: Given a claim, if I want to verify the truth or falseness of the claim, help me extract the entities of the claim to be more suitable for knowledge graph to search for evidence. The entities should be short and no more than 5.
Only entities such as proper names, places, and person need to be extracted, ignoring entities such as time, data, numbers, country, and verbs.
If there is no suitable entity just answer None.
Claim: {claim}
Entities: ["Entity 1", "Entity 2"...]
Remember to follow the format for output.
"""

CHOOSE_RELEVANT_PATH = """Based on the claim, extract the most relevant results from the following search results and only return their indices, with no more than three indices:
Claim: {claim}
Search results: {combined_strings}
Idx: ['idx1', ...]
Remember to follow the format for output. For example: Idx: ['idx1']
"""

CHOOSE_FINAL_PATH = """Based on the results retrieved from the following knowledge graph, choose some of the most relevant path to claim and only return their indices:
Claim: {claim}
Results: {result_chain}
Idx: ['idx1', ...]
Remember to follow the format for output. For example: Idx: ['idx1', 'idx2', 'idx3']
"""

INFORMATION_EVALUATION = """Information: {result_chain}
Claim: {claim}
Is the above information sufficient to validate the claim? Only answer yes or no. Don't generate anything else, for example: Yes.
"""

PROCESS_KG = """Convert each of the following pieces of information retrieved from the Knowledge Graph into a natural statement separately.
Please response according to the following example, do not generate other irrelevant information. For example:
Information:[
"Entity: The Kentucky Department of Corrections, Relation: headquarters location, TargetEntity: Frankfort -> Entity: Frankfort, Relation: located in or next to body of water, TargetEntity: Kentucky River",
"Entity: the Kentucky River, Relation: located in the administrative territorial entity, TargetEntity: Kentucky -> Entity: Kentucky, Relation: named after, TargetEntity: Kentucky River",
"Entity: the Kentucky River, Relation: drainage basin, TargetEntity: Kentucky River drainage basin -> Entity: Kentucky River drainage basin, Relation: located in or next to body of water, TargetEntity: Kentucky River"
]
Output:
1.The Kentucky Department of Corrections has its headquarters located in Frankfort, which is situated next to the Kentucky River.
2.The Kentucky River is located in Kentucky, and the state of Kentucky is named after the Kentucky River.
3.The Kentucky River drainage basin includes the Kentucky River.

Information: {KG_results}
Output:
"""

GENERATE_SUMMARY = """As a paragraph-summarizing assistant, you are required to complete the task according to the following rules:
1. Extract information related to the claim from the provided paragraphs and summarize it; the summary should not exceed 300 words.
2. Summarize all the information in the paragraphs that is relevant to the claim, but do not generate a summary based directly on the claim, as the claim may be incorrect.
3. Summary should be accurate and comprehensive.
4. Do not summarize irrelevant information.
5. Do not generate information that is not relevant to summary.

Claim: {claim}
Paragraph1: {paragraph1}
Paragraph2: {paragraph2}
"""

GENERATE_EVIDENCE = """As an Information Retrieval Assistant, you are required to complete the task according to the following rules:
1. Based on the given information, retrieve 3 additional pieces of information that can help determine the correctness of the claim.
2. Each piece of additional information should not exceed 100 words.
3. Do not generate additional information directly based on the claim, as the claim may be incorrect.
4. If there is an error in the given information, please provide the correct information as additional information.

Claim: {claim}
Summary: {summary}
Additional information: 
"""


VERIFY_CLAIM = """"Evidence of Summary:
{summary}

Evidence of LLM:
{llm_evidence}

Based on the above information, is it true that {claim}? True or false? The answer is: 
"""