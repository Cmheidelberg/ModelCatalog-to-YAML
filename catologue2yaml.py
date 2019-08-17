import requests
import yaml
import click
import argparse
import logging
import os

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG if os.getenv("WINGS_DEBUG", False) else logging.INFO)


def make_yaml(url,file_path=None):

    # sets path, this determines where the component will be downloaded. Default is the current directory of the program
    if file_path is None:
        path = os.getcwd()
    else:
        path = file_path

    fold_name = url.split('/')
    fold_name = fold_name[-1]
    path = os.path.join(path,fold_name)

    if os.path.exists(path):
        click.echo("\"" + path + "\" already exists. Do you want to overwrite it? [y/n]")
        ans = input()
        if ans.lower() == 'y' or ans.lower() == "yes":
            shutil.rmtree(path)
        else:
            logger.info("Aborting Download")
            exit(0)

    os.mkdir(path)

    param_input = url # 'https://w3id.org/okn/i/mint/pihm-v2'

    logger.info("Requesting data")
    mc_params = {
        'modelConfig': param_input
    }

    params = {
        'config': param_input
    }

    metadata = requests.get(
        'https://query.mint.isi.edu/api/dgarijo/MINT-ModelCatalogQueries/getModelConfigurationMetadata',
        params=mc_params
    )

    parameters = requests.get(
        'https://query.mint.isi.edu/api/dgarijo/MINT-ModelCatalogQueries/getConfigIParameters'
        , params=params
    )

    io = requests.get(
        'https://query.mint.isi.edu/api/dgarijo/MINT-ModelCatalogQueries/getConfigI_OVariables'
        , params=params
    )

    # print("\nMETADATA")
    # print(metadata.text)
    # print("\nPARAMETERS")
    #print(parameters.text)
    # print("\nINPUT OUTPUT VARS")
    # print(io.text)

    yaml_meta = {}
    yaml_wings = {}

    metadata = metadata.json()
    parameters = parameters.json()
    io = io.json()

    # If any of the requests return nothing quit

    empty_input = False

    if not ((metadata["results"])["bindings"]):
        logger.error("ModelConfigurationMetadata empty")
        empty_input = True

    if not ((parameters["results"])["bindings"]):
        logger.error("ConfigIParameters empty")
        empty_input = True

    if not ((io["results"])["bindings"]):
        logger.error("ConfigI_OVariables empty")
        empty_input = True

    # Quits if any of the requests are empty
    if empty_input:
       logger.info("Aborting")
       exit(0)

    metadata = ((metadata["results"])["bindings"])[0]
    parameters = ((parameters["results"])["bindings"])
    io = ((io["results"])["bindings"])

    default_info = param_input.split('/')
    default_info = default_info[-1]
    default_info = default_info.split('-')

    yaml_meta["name"] = default_info[0]

    yaml_meta["version"] = default_info[1]

    # Unneeded, but helpful data: description, author, keywords, label
    yaml_meta["description"] = (metadata["desc"])["value"]

    author_name = ((metadata["authors"])["value"]).split("/")
    author_name = author_name[-1]
    yaml_meta["author"] = [author_name]

    keywords = (metadata["keywords"])["value"]
    keywords = keywords.split(';')

    # remove first whitespace from applicable keywords
    count = 0
    for i in keywords:
        if i[0].isspace():
            i = i[1:]
            keywords[count] = i
        count += 1

    yaml_meta["keywords"] = keywords
    yaml_meta["label"] = (metadata["label"])["value"]

    data = {}
    inputs = []
    outputs = []
    for i in io:
        curr_io = {}
        find_if_input = (i["prop"])["value"]
        find_if_input = find_if_input.split("#")
        itype = ((i["type"])["value"]).split('#')

        # prefix = prefix + (i["position"])["value"]

        curr_io["role"] = (i["iolabel"])["value"]
        curr_io["isParam"] = False
        curr_io["type"] = "dcdom:" + itype[-1]
        curr_io["dimensionality"] = int((i["dim"])["value"])

        #sets up data
        data[itype[-1]] = {}
        (data[itype[-1]])["files"] = []

        if find_if_input[-1] == "hasInput":
            prefix = "-i" + str((i["position"])["value"])
            curr_io["prefix"] = prefix
            inputs.append(curr_io)

        elif find_if_input[-1] == "hasOutput":
            prefix = "-o" + str((i["position"])["value"])
            curr_io["prefix"] = prefix
            outputs.append(curr_io)
        else:
            logger.warning(find_if_input[-1] + " is unknown IO type")

    for p in parameters:
        curr_par = {}
        prefix = "-p" + str((p["position"])["value"])
        # prefix = prefix +

        curr_par["role"] = (p["paramlabel"])["value"]
        curr_par["isParam"] = True
        curr_par["type"] = "xsd:" + (p["pdatatype"])["value"]
        # curr_par["dimensionality"] = int((p["dim"])["value"])
        curr_par["dimensionality"] = 0

        curr_par["prefix"] = prefix
        curr_par["paramDefaultValue"] = (p["defaultvalue"])["value"]

        inputs.append(curr_par)
        count += 1

    yaml_wings["inputs"] = inputs
    yaml_wings["outputs"] = outputs
    rules = [1]
    rules[0] = (metadata["constraints"])["value"]
    yaml_wings["rules"] = rules

    src = ["src\\*"]
    yaml_wings["src"] = src

    yaml_wings["componentType"] = "Component"
    yaml_wings["data"] = data


    yaml_meta["wings"] = yaml_wings

    stream = open(os.path.join(path,"wings-component.yaml"), 'w+')
    yaml.dump(yaml_meta, stream, sort_keys=False)

    logger.info("Generated YAML")

def _main():
    parser = argparse.ArgumentParser(
        description="Downloads component from the Model Catalog given the components url"
    )
    parser.add_argument(
        "--file-path",
        "-f",
        type=str,
        default=None,
    )
    parser.add_argument("url", help="URL of component")
    args = parser.parse_args()

    make_yaml(**vars(args))

    logger.info("Done")


if __name__ == "__main__":
    try:
        _main()
    except Exception as e:
        logger.exception(e)
