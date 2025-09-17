import os
import json
import argparse
import re
import time
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from utils.llm import LLMRequester
from utils.prompt import EXTRACT_ENTITIES,CHOOSE_RELEVANT_PATH, CHOOSE_FINAL_PATH, INFORMATION_EVALUATION

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_name', default='FEVEROUS', type=str)
    parser.add_argument('--model_name', default='gpt-3.5-turbo',type=str)
    args = parser.parse_args()
    return args


class KGSearcher():
    def __init__(self):
        self.llm = LLMRequester()
        self.args = parse_args()
        self.dataset_name = self.args.dataset_name
        self.model = self.args.model_name


    def extract_entities(self, claim):
        prompt = EXTRACT_ENTITIES.format(claim=claim)
        response = self.llm.generate(self.model, prompt)
        match = re.search(r'Entities: (\[.*?])', response)
        entities_list = []
        if match:
            entities_str = match.group(1)
            entities_list = eval(entities_str)  
        return entities_list
    
    def get_entity_name(self, entityID):
        attempt = 0
        while attempt < 3:
            try:
                url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={entityID}"
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                data = response.json()
                # Extract the entity name
                entity = data["entities"][entityID]
                entity_name = entity["labels"]["en"]["value"]
                return entity_name
            except:
                attempt += 1
                time.sleep(10)
                continue
        return None
    
    def get_entity_ID(self, entity_name):
        attempt = 0
        while attempt < 3:
            try:
                url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&language=en&format=json&search={entity_name}"
                response = requests.get(url,headers={'User-Agent': 'Mozilla/5.0'})
                data = response.json()
                return data['search'][0]['id']
            except:
                attempt += 1
                time.sleep(10)
                continue
        return None
    
    def get_entity_description(self, entityID):
        attempt = 0
        while attempt < 3:
            try:
                url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={entityID}"
                response = requests.get(url,headers={'User-Agent': 'Mozilla/5.0'})
                data = response.json()
                # Extract the entity name
                entity = data["entities"][entityID]
                entity_description = entity.get("descriptions", {}).get("en", {}).get("value", 'None')
                aliases = entity.get("aliases", {}).get("en", [])
                entity_aliases = 'None'
                if aliases:
                    entity_aliases = "; ".join(alias["value"] for alias in aliases)
                return entity_description, entity_aliases
            except:
                attempt += 1
                time.sleep(10)
                continue
        return 'None', 'None'

    def entity_search(self, entityID):
        attempt = 0
        while attempt < 3:
            try:
                endpoint_url = "https://query.wikidata.org/sparql"
                query = f"""
                SELECT ?relation ?propertyLabel ?entity ?entityLabel WHERE {{
                    wd:{entityID} ?relation ?entity .
                    ?property wikibase:directClaim ?relation .
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                    OPTIONAL {{
                        ?entity rdfs:label ?entityLabel .
                        FILTER (LANG(?entityLabel) = "en")
                    }}
                }}"""
                sparql = SPARQLWrapper(endpoint_url)
                sparql.setQuery(query)
                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()
                return results
            except Exception:
                attempt += 1
                time.sleep(10)
                continue
        return None


    def extract_results(self, search_result):
        result_list = []
        max_results = 100  # 最大结果数
        filter_list = ['ID', 'image', 'website', 'followers', 'ISNI', 'username', 'audio', 'entity code','URL']

        count = 0
        for item in search_result['results']['bindings']:
            relationID = item['relation']['value'].split('/')[-1]  # 提取relation的ID
            entity_value = item['entity']['value'].split('/')[-1]  # 提取entity的ID

            # 检查relationID是否类似于P213形式
            if re.match(r'^P\d+$', relationID) and not any(f in item['propertyLabel']['value'] for f in filter_list):
                entityID_match = re.match(r'^Q\d+$', entity_value)
                result = {
                    'relationID': relationID,
                    'relationLabel': item['propertyLabel']['value'],
                    'entityID': entityID_match.group() if entityID_match else 'None',
                    'entityLabel': item['entityLabel']['value']
                }
                result_list.append(result)
                count += 1

            if count >= max_results:
                break

        return result_list

    def combine_info(self, entityID, entity_name, info_list):
        combined_strings = []
        for idx, info in enumerate(info_list):
            combined_string = f"idx{idx}, Relation: {info['relationLabel']}, TargetEntity: {info['entityLabel']}"
            combined_strings.append(combined_string)

        entity_description, entity_aliases = self.get_entity_description(entityID)

        combined_dict = {
            'entity_info': f'Entity: {entity_name}, Description: {entity_description}, Aliases: {entity_aliases}',
            'results': combined_strings,
        }
        return combined_dict
    
    def parse_string_info(self, s, idx, search_result):
        target_entityID = search_result[idx]['entityID']
        pattern = r'Relation:\s*(.*?),\s*TargetEntity:\s*(.*)'
        match = re.search(pattern, s)

        if not match:
            return None

        entity, relation, target_entity = map(str.strip, match.groups())

        if not (entity and relation and target_entity):
            return None
        return target_entityID, entity, relation, target_entity
    
    def choose_relevant_path(self, claim, combined_strings):
        prompt = CHOOSE_RELEVANT_PATH.format(claim=claim, combined_strings=combined_strings)
        response = self.llm.generate(self.model, prompt)
        pattern = r"Idx:\s*(\['.*?'\])"
        match = re.search(pattern, response)
        indices_list = []
        if match:
            list_str = match.group(1)
            indices_list = eval(list_str)
        return indices_list

    def information_evaluation(self, claim, result_strings):
        prompt = INFORMATION_EVALUATION.format(result_chain=result_strings, claim=claim)
        response = self.llm.generate(self.model, prompt)
        return response.strip().lower() == "yes"


    def combine_result_chain(self, claim, current_path, current_level, max_level, searched_entities):
        result_strings = [" -> ".join(
            [f"Entity: {entity}, Relation: {relation}, TargetEntity: {target_entity}" for _, entity, relation, target_entity in current_path])]

        flag = self.information_evaluation(claim, result_strings)

        if current_level == max_level or flag:
            return flag, [current_path]

        entityID = current_path[-1][1]
        last_entity = current_path[-1][3]

        if entityID in searched_entities or entityID == 'None':
            return False, [current_path]

        searched_entities.add(entityID)
        next_search_result = self.entity_search(entityID)

        if next_search_result is None:
            return False, [current_path]

        next_parsed_result = self.extract_results(next_search_result)
        next_combined_dict = self.combine_info(entityID, last_entity, next_parsed_result)
        next_response = self.choose_relevant_path(claim, next_combined_dict['results'])

        if next_response is None:
            return False, [current_path]

        next_indices = [int(re.search(r'\d+', idx).group()) for idx in next_response]

        results = []
        for idx in next_indices:
            if 0 <= idx < len(next_parsed_result):
                next_entity_info = next_combined_dict['entity_info']

                next_target_entity = next_parsed_result[idx]
                next_target_entityID = next_target_entity['entityID']
                next_relation = next_target_entity['relationLabel']
                next_target_entity_name = next_target_entity['entityLabel']

                next_path = current_path + [(next_entity_info, next_target_entityID, next_relation, next_target_entity_name)]
                sub_flag, sub_results = self.combine_result_chain(claim, next_path, current_level + 1, max_level, searched_entities)
                results.extend(sub_results)
                if sub_flag:
                    flag = True
                    break

        return flag, results
    
    def final_path(self, claim, result_chain):
        prompt = CHOOSE_FINAL_PATH.format(claim=claim, result_chain=result_chain)
        response = self.llm.generate(self.model, prompt)
        pattern = r"Idx:\s*(\['.*?'\])"
        match = re.search(pattern, response)
        indices_list = []
        if match:
            list_str = match.group(1)
            indices_list = eval(list_str)
        return indices_list


def main():
    args = parse_args()
    dataset_name = args.dataset_name
    model = args.model_name
    KG_searcher = KGSearcher()
    evidence_result = []
    outputs = []
    wikidata_evidences = {}
    searched_entities = set()


    with open(os.path.join('./datasets', dataset_name, 'claims', 'dev.json'), 'r') as f:
        raw_data = json.load(f)
    

    for idx, sample in enumerate(raw_data):
        wikidata_evidence = {'idx': idx,
                            'id': sample['id'],
                            'claim': sample['claim'],
                            'wikidata_evidence': []}
        wikidata_evidences[sample['id']] = wikidata_evidence

        claim = sample['claim']

        entity_list = KG_searcher.extract_entities(claim)
        # print(idx, claim)

        global_gpt_times = 0
        final_result = []
        relevant_path_lst = []

        if not entity_list:
            continue

        for initial_entity in entity_list:
            stop_flag = False

            initial_entityID = KG_searcher.get_entity_ID(initial_entity)
            if initial_entityID is None or stop_flag or initial_entityID in searched_entities:
                continue

            searched_entities.add(initial_entityID)
            initial_search_result = KG_searcher.entity_search(initial_entityID)
            search_result = KG_searcher.extract_results(initial_search_result)
            combined_dict = KG_searcher.combine_info(initial_entityID, initial_entity, search_result)

            response = KG_searcher.choose_relevant_path(claim, combined_dict)
            if response is None:
                continue

            indices = [int(re.search(r'\d+', idx).group()) for idx in response]

            max_level = 2
            results = []
            results_chain = []
            for idx in indices:
                results_chain = []
                if stop_flag:
                    break
                if 0 <= idx < len(search_result):
                    entity_info = combined_dict['entity_info']

                    target_entity = search_result[idx]
                    target_entityID = target_entity['entityID']
                    relation = target_entity['relationLabel']
                    target_entity_name = target_entity['entityLabel']

                    current_path = [entity_info, target_entityID, relation, target_entity_name]

                    flag, sub_results = KG_searcher.combine_result_chain(claim, [current_path], 1, max_level, searched_entities)
                    results.extend(sub_results)
                    result_strings = [" -> ".join(
                        [f"{entity_info}, Relation: {relation}, TargetEntity: {target_entity_name}" for entity_info, _, relation, target_entity_name in path]) for path in results]
                    results_chain.append(result_strings)
                    if flag:
                        stop_flag = True

            final_result.extend(results_chain)

        formatted_results_chains = []
        if final_result:
            for idx, sublist in enumerate(final_result):
                new_sublist = []

                for index, item in enumerate(sublist):
                    formatted_item = f"idx{index}: {item}"
                    new_sublist.append(formatted_item)

                formatted_results_chains.append(new_sublist)

        for formatted_results_chain in formatted_results_chains:
            relevant_path_idx = KG_searcher.final_path(claim, formatted_results_chain)
            if relevant_path_idx is None:
                continue
            indices = [int(re.search(r'\d+', idx).group()) for idx in relevant_path_idx]

            for idx in indices:
                if 0 <= idx < len(formatted_results_chain):
                    relevant_path = formatted_results_chain[idx]
                    match_details = re.search(r'idx\d+: (.*)', relevant_path)
                    if match_details:
                        relevant_path_lst.append(match_details.group(1))

        # print('gpt times:', global_gpt_times)
        # print(relevant_path_lst)
        wikidata_evidences[sample['id']]['wikidata_evidence'] = relevant_path_lst
        output_file_path = f'./data/{dataset_name}_KG_original_evidence.json'
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r', encoding='utf-8') as f:
                outputs = json.load(f)
        outputs.append(wikidata_evidences[sample['id']])
        sorted_outputs = sorted(outputs, key=lambda x: x['idx'])
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_outputs, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

