import requests
import yaml

paramInput = 'https://w3id.org/okn/i/mint/pihm-v2'

mcParams = {
    'modelConfig': paramInput
}

params = {
    'config': paramInput
}

metadata = requests.get(
    'https://query.mint.isi.edu/api/dgarijo/MINT-ModelCatalogQueries/getModelConfigurationMetadata',
    params=mcParams
)

parameters = requests.get(
    'https://query.mint.isi.edu/api/dgarijo/MINT-ModelCatalogQueries/getConfigIParameters'
    , params=params
)

io = requests.get(
    'https://query.mint.isi.edu/api/dgarijo/MINT-ModelCatalogQueries/getConfigI_OVariables'
    , params=params
)

print("\nMETADATA")
print(metadata.text)
print("\nPARAMETERS")
print(parameters.text)
print("\nINPUT OUTPUT VARS")
print(io.text)

yamlMeta = {}
yamlWings = {}

metadata = metadata.json()
parameters = parameters.json()
io = io.json()

metadata = ((metadata["results"])["bindings"])[0]
io = ((io["results"])["bindings"])
parameters = ((parameters["results"])["bindings"])

defaultInfo = paramInput.split('/')
defaultInfo = defaultInfo[-1]
defaultInfo = defaultInfo.split('-')

yamlMeta["name"] = defaultInfo[0]

# Remove all non-numbers from the version
defaultInfo[1] = ''.join([c for c in defaultInfo[1] if c in '1234567890.'])
yamlMeta["version"] = defaultInfo[1]

# Unneeded, but helpful data: description, author, keywords, label
yamlMeta["description"] = (metadata["desc"])["value"]

authorName = ((metadata["authors"])["value"]).split("/")
authorName = authorName[-1]
yamlMeta["author"] = authorName

keywords = (metadata["keywords"])["value"]
keywords = keywords.split(';')

# remove first whitespace from applicable keywords
count = 0
for i in keywords:
    if i[0].isspace():
        i = i[1:]
        keywords[count] = i
    count += 1

yamlMeta["keywords"] = keywords
yamlMeta["label"] = (metadata["label"])["value"]

inputs = []
outputs = []
icount = 1
ocount = 1
for i in io:
    currIO = {}
    findIfInput = (i["prop"])["value"]
    findIfInput = findIfInput.split("#")
    itype = ((i["type"])["value"]).split('#')

    # prefix = prefix + (i["position"])["value"]

    currIO["role"] = (i["iolabel"])["value"]
    currIO["isParam"] = False
    currIO["type"] = "dcdom:" + itype[-1]
    currIO["dimensionality"] = int((i["dim"])["value"])

    if findIfInput[-1] == "hasInput":
        prefix = 'i'
        prefix = "-" + prefix + str(icount)
        currIO["prefix"] = prefix
        inputs.append(currIO)
        icount += 1

    elif findIfInput[-1] == "hasOutput":
        prefix = 'o'
        prefix = "-" + prefix + str(ocount)
        currIO["prefix"] = prefix
        outputs.append(currIO)
        ocount += 1
    else:
        print(findIfInput[-1] + " is unknown IO type")

count = 1
for p in parameters:
    currPar = {}
    prefix = "p"

    prefix = "-" + prefix + str(count)
    # prefix = prefix + (p["position"])["value"]

    currPar["role"] = (p["paramlabel"])["value"]
    currPar["isParam"] = True
    currPar["type"] = "xsd:" + (p["pdatatype"])["value"]
    currPar["prefix"] = prefix
    currPar["paramDefaultValue"] = (p["defaultvalue"])["value"]

    inputs.append(currPar)
    count += 1

yamlWings["inputs"] = inputs
yamlWings["outputs"] = outputs

yamlWings["rules"] = (metadata["constraints"])["value"]
src = ["src\\*"]
yamlWings["src"] = src

yamlWings["componentType"] = "Component"

yamlMeta["wings"] = yamlWings
stream = open("wings-component.yaml", 'w+')
yaml.dump(yamlMeta, stream, sort_keys=False)
