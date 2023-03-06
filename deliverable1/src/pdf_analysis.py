import argparse
import json
import os
import re
import shutil
from time import sleep

import nltk
import requests
from nltk.corpus import stopwords
import wordcloud
import logging
import xml
from grobid_client.grobid_client import GrobidClient
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

logging.basicConfig(filename=f'./log.log', encoding='utf-8', format='%(asctime)s %(message)s',
                    level=logging.DEBUG)


def get_namespace(tree):
    '''
    This function gets the namespace of a given XML tree.
    :param tree: an ElementTree object
    :return: the namespace string
    '''
    res = list(map(lambda x: x.split("}")[0] + "}" if "}" in x else "",
                   filter(lambda x: "namespace" in x, tree.getroot().attrib.keys())))
    return res[0] if len(res) > 0 else ""


def get_schema(tree):
    '''
    This function gets the schema of a given XML tree.
    :param tree: an ElementTree object
    :return: the schema string
    '''

    res = tree.getroot().tag.split("}")
    return res[0] + "}" if len(res) > 0 else ""


def delete_failures(output):
    '''
    This function deletes the files with "_500" in the name from the output directory.
    '''
    failures = map(lambda x: x.strip("_500"), filter(lambda x: x.endswith(".txt"), os.listdir(output)))
    for failure in failures:
        try:
            os.remove(output_dir + "/" + failure)
            logging.info(f"Deleted {failure}")
        except:
            logging.info(f"Could not delete {failure}")


def get_stopwords(languages):
    '''
    This function gets stopwords for the given languages.
    :param languages: a set of language codes
    :return: a set of stopwords
    '''
    bag = set()
    for language in languages:
        if "es" in language:
            bag.update(set(nltk.corpus.stopwords.words("spanish")))
        if "en" in language:
            bag.update(set(nltk.corpus.stopwords.words("english")))
        if "fr" in language:
            bag.update(set(nltk.corpus.stopwords.words("french")))
        if "de" in language:
            bag.update(set(nltk.corpus.stopwords.words("german")))
        if "it" in language:
            bag.update(set(nltk.corpus.stopwords.words("italian")))
        if "pt" in language:
            bag.update(set(nltk.corpus.stopwords.words("portuguese")))
    return bag


def get_abstract(papers, elem, schema):
    '''
    This function gets the abstract of a given paper.
    :param papers: a dictionary of papers
    :param elem: the name of the XML file containing the paper
    :param schema: the schema string
    :return: the abstract string
    '''
    if papers[elem].find(f"{schema}teiHeader") is not None:
        if papers[elem].find(f"{schema}teiHeader").find(f"{schema}profileDesc") is not None:
            if papers[elem].find(f"{schema}teiHeader").find(f"{schema}profileDesc").find(
                    f"{schema}abstract") is not None:
                return ET.tostring(
                    papers[elem].find(f"{schema}teiHeader").find(f"{schema}profileDesc").find(f"{schema}abstract"),
                    encoding='utf-8', method='text').strip().decode("utf-8")
    return ""


def get_langauge(papers, elem, schema, namespace):
    '''
    Returns the language of a given element in a TEI document, if available.

    :param papers: list. A list of parsed TEI documents.
    :param elem: int. Index of the element in the `papers` list whose language we want to retrieve.
    :param schema: str. The schema used to define the TEI document, e.g. "tei:" or "tei2:".
    :param namespace: str. The namespace used to define the TEI document, e.g. "xml:" or "tei:".

    :returns:language: str or None
        The language of the element, as specified in the TEI header, or None if no language is specified.
    '''
    if papers[elem].getroot().find(f"{schema}teiHeader") is not None:
        if f"{namespace}lang" in papers[elem].getroot().find(f"{schema}teiHeader").attrib.keys():
            return papers[elem].getroot().find(f"{schema}teiHeader").attrib[f"{namespace}lang"]
    return None


def dump_links(output_dir, links):
    '''
    Dumps a dictionary of links to a JSON file.

    :param: links: dict
        A dictionary of links to dump.
    '''
    with open(f'{output_dir}/links.txt', 'w') as f:
        f.write(json.dumps(links, default=str, indent=4))
    logging.info(f"Dumped links to {output_dir}/links.txt")


def plot_wordcloud(output_dir, abstracts, stopwords=None):
    '''
    Generates a word cloud from a collection of abstracts and saves it to a PNG file.

    :param:abstracts: str
        A string containing the text of the abstracts to use for the word cloud.
    :param stopwords: set or None
        A set of words to exclude from the word cloud. If None, the default stopword list is used.
    '''
    if abstracts == "":
        logging.warning("No abstracts to generate wordcloud from.")
        return
    wordcloud.wordcloud.WordCloud(stopwords=stopwords).generate(abstracts).to_file(f'{output_dir}/wordcloud.png')
    logging.info(f"Dumped wordcloud to {output_dir}/wordcloud.png")


def plot_num_figures(output_dir, figures):
    '''
    Plots a bar chart of the number of figures in each article and saves it to a PNG file.

    :param  figures: dict
        A dictionary mapping article IDs to the number of figures in each article.
    '''
    figure_keys = sorted(figures, reverse=True)
    figure_vals = [figures[key] for key in figure_keys]
    plt.figure(figsize=(30, 10))
    plt.bar(figure_keys, figure_vals)
    plt.title("Number of figures per article")
    plt.xlabel("Article")
    plt.ylabel("Number of figures")
    plt.subplots_adjust(bottom=0.4)
    plt.xticks(rotation=45)
    plt.savefig(f'{output_dir}/figures.png')
    logging.info(f"Dumped figures to {output_dir}/figures.png")


def healthcheck(server):
    '''
    Checks if the grobid server is healthy.
    :param server: the grobid server url
    '''

    def request(srv):
        try:
            return bool(requests.get(f"{srv}/api/isalive").content.decode().capitalize())
        except:
            return False

    max_retries = 4
    attempt = 0
    while not request(server):
        attempt = attempt + 1
        sleep(10)
        if attempt >= max_retries:
            logging.error("Could not connect to grobid")
            exit(1)
    logging.info("Grobid HEALTHY")


def extract(output_dir, stopwords=False):
    '''
    Extracts information from XML files in the output directory.
    '''
    languages = set()
    papers = {}
    abstracts = {}
    figures = {}
    links = {}
    for elem in os.listdir(output_dir):
        logging.info(f"Trying to process {output_dir}/{elem}")
        if not elem.endswith(".xml"):
            continue
        try:
            papers[elem] = ET.parse(output_dir + "/" + elem)
        except:
            continue
        namespace = get_namespace(papers[elem])
        schema = get_schema(papers[elem])
        languages.add(get_langauge(papers, elem, schema, namespace))
        abstracts[elem] = get_abstract(papers, elem, schema)
        aux = papers[elem].findall(f".//{schema}figure")

        figures[elem] = len(aux) if aux is not None else 0
        aux = papers[elem].findall(f"{schema}ptr")
        text = ET.tostring(papers[elem].getroot(), encoding='utf8', method='text').strip()
        aux.extend(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                              text.decode()))
        links[elem] = aux

    wordbag = get_stopwords(languages) if stopwords else None
    plot_num_figures(output_dir, figures)
    dump_links(output_dir, links)
    plot_wordcloud(output_dir, " ".join(abstracts.values()), stopwords=wordbag)
    save_summary(output_dir, figures, links)


def save_summary(output_dir, figures, links):
    '''
    Saves a summary of the extracted information to a JSON file.
    :param figures: dict
        A dictionary mapping article IDs to the number of figures in each article.
    :param links: dict
        A dictionary mapping article IDs to a list of links in each article.
    '''
    summary = {}
    for elem in figures:
        summary[elem] = {"figures": figures[elem], "links": links[elem]}
    with open(f'{output_dir}/summary.json', 'w') as f:
        f.write(json.dumps(summary, default=str, indent=4))
    logging.info(f"Dumped summary to {output_dir}/summary.json")


def main(input_dir, output_dir, grobid_client_config_path):
    open(f"log.log", "w").close()

    cleanup_output_dir(output_dir)

    stopwords_available = True
    try:
        nltk.download('stopwords', raise_on_error=True)
    except:
        stopwords_available = False
        logging.warning("NLTK stopwords not available. Wordcloud will not be generated")

    with open(grobid_client_config_path, "r") as fp:
        config = json.load(fp)

    healthcheck(config["grobid_server"])

    client = GrobidClient(config_path=grobid_client_config_path)
    client.process("processFulltextDocument",
                   input_path=input_dir,
                   n=20,
                   output=output_dir,
                   consolidate_citations=True,
                   verbose=False
                   )

    delete_failures(output_dir)
    extract(output_dir, stopwords_available)


def cleanup_output_dir(output_dir):
    '''
    Deletes all files in the output directory.
    '''
    for elem in os.listdir(output_dir):
        os.remove(f"{output_dir}/{elem}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='PDF Analysis',
        description='Analyse PDFs using GROBID',
    )
    parser.add_argument(
        '--INPUT_PATH',
        default="./input_files",
        required=False,
        help='Path to the input directory containing the PDFs to be analysed',
    )
    parser.add_argument(
        '--OUTPUT_PATH',
        default="./output_files",
        required=False,
        help='Path to the output directory where the results will be stored',
    )
    parser.add_argument(
        "--GROBID_CLIENT_CONFIG_PATH",
        default="./config.json",
        required=False,
        help="Path to the GROBID client configuration file",
    )
    args = parser.parse_args()
    grobid_client_config_path = args.GROBID_CLIENT_CONFIG_PATH
    input_dir = args.INPUT_PATH
    output_dir = args.OUTPUT_PATH

    main(input_dir, output_dir, grobid_client_config_path)
