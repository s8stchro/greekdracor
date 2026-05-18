import os
import json
import lxml.etree as ET
import networkx as nx
from glob import glob

def parse_play(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    ns = {'tei': 'http://www.tei-c.org/ns/1.0', 'xml': 'http://www.w3.org/XML/1998/namespace'}

    play_id = root.get('{http://www.w3.org/XML/1998/namespace}id')
    title_elem = root.find('.//tei:titleStmt/tei:title', ns)
    title = title_elem.text if title_elem is not None else os.path.basename(filepath)

    author_elem = root.find('.//tei:titleStmt/tei:author/tei:persName', ns)
    if author_elem is None:
        author_elem = root.find('.//tei:titleStmt/tei:author', ns)
    author = author_elem.text if author_elem is not None else "Unknown"

    characters = {}
    for person in root.xpath('.//tei:person|.//tei:personGrp', namespaces=ns):
        char_id = person.get('{http://www.w3.org/XML/1998/namespace}id')
        name = person.find('./tei:persName', ns)
        if name is None:
            name = person.find('./tei:name', ns)

        name_text = name.text if name is not None else char_id
        sex = person.get('sex', 'UNKNOWN')
        characters[char_id] = {'id': char_id, 'name': name_text, 'sex': sex}

    # Identify interaction segments based on speeches
    # We use a simple strategy: find all speeches and identify which div they belong to.
    # To mimic DraCor's co-occurrence (characters in same scene), we'll use the
    # smallest div containing the speech.

    # Actually, a better approach for DraCor-like network is often based on scenes.
    # In these TEIs, scenes are not always clearly marked with a "scene" type,
    # but div1/div2 often represent structural units.

    # Let's collect all sp elements and their immediate structural parent div.
    # Then group speakers by that parent div.

    segment_speakers = {}
    for sp in root.xpath('.//tei:sp', namespaces=ns):
        who = sp.get('who')
        if not who:
            continue

        # Find the smallest ancestor div
        parent_div = sp.xpath('./ancestor::*[starts-with(local-name(), "div")][1]')
        if not parent_div:
            # If no div ancestor, use the body or something else?
            # Should not happen in well-formed TEI drama.
            div_id = "root"
        else:
            div_id = id(parent_div[0])

        if div_id not in segment_speakers:
            segment_speakers[div_id] = set()

        for w in who.split():
            char_id = w.lstrip('#')
            if char_id in characters:
                segment_speakers[div_id].add(char_id)

    # Build network
    G = nx.Graph()
    for char_id in characters:
        G.add_node(char_id)

    for speakers in segment_speakers.values():
        speaker_list = list(speakers)
        for i in range(len(speaker_list)):
            for j in range(i + 1, len(speaker_list)):
                u, v = speaker_list[i], speaker_list[j]
                if G.has_edge(u, v):
                    G[u][v]['weight'] += 1
                else:
                    G.add_edge(u, v, weight=1)

    # Calculate metrics
    metrics = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
        'density': nx.density(G),
        'clustering': nx.average_clustering(G) if G.number_of_nodes() > 1 else 0,
    }

    if G.number_of_nodes() > 1:
        degree_centrality = nx.degree_centrality(G)
        betweenness = nx.betweenness_centrality(G)
    else:
        degree_centrality = {n: 0 for n in G.nodes()}
        betweenness = {n: 0 for n in G.nodes()}

    for char_id in characters:
        characters[char_id]['degree'] = degree_centrality.get(char_id, 0)
        characters[char_id]['betweenness'] = betweenness.get(char_id, 0)

    # Prepare node and edge lists
    node_list = [data for data in characters.values()]
    edge_list = [{'source': u, 'target': v, 'weight': d['weight']} for u, v, d in G.edges(data=True)]

    return {
        'id': play_id,
        'title': title,
        'author': author,
        'metrics': metrics,
        'network': {
            'nodes': node_list,
            'edges': edge_list
        }
    }

def main():
    corpus = []
    files = sorted(glob('tei/*.xml'))
    for f in files:
        print(f"Parsing {f}...")
        try:
            play_data = parse_play(f)
            corpus.append(play_data)
        except Exception as e:
            print(f"Error parsing {f}: {e}")

    with open('corpus_data.json', 'w', encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    print(f"Done! Parsed {len(corpus)} plays. Saved to corpus_data.json")

if __name__ == '__main__':
    main()
