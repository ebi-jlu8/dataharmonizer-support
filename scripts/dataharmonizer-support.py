#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
script to create the export.js and schema.yaml file for DataHarmonizer to generate generate templates in DataHarmonizer
"""
import re
import os
import glob
from functools import reduce
import argparse
from collections import OrderedDict, Counter
import sys
import numpy as np
import pandas as pd
import requests
import time
from io import StringIO
import csv
import random
import subprocess
import yaml
import warnings
from pathlib import Path
import json

#coordinates (long, lat) of 18 mouse facilities
#center_code: ["institute-facility", "microbial_status", lat, long] - revise with actual codes and coords from the 18 established mouse facilities.
facility_coords = {
    "MLC": ["MRC Harwell-Mary Lyons Centre", "SPF", 51.5757261889298, -1.3197682153434656], #Mary Lyons Center (OXF)
    "FCI": ["Francis Crick Institute-aimal facility", "SPF", 51.531641682446555, -0.12872668895589073], #
    "WSI": ["Wellcome Sanger Institute-animal facility", "SPF", 52.078602499359974, 0.18642799638762686], #Sanger Institute
    "CCVS": ["UE Queen's Medical Research Institute-Centre for Cardiovascular Science", "SPF", 55.92262196891785, -3.1389381809648262], #University of Edinburgh
    "OXBSB": ["Oxford Biomedial Services Building", "SPF", 51.75855708548558, -1.2525512176093105],
    "UBS": ["Cambridge University Biomedical Services", "SPF", 52.17272216502203, 0.13264658096482684],
    "KCLARF": ["King's College London-Animal Research Facility", "SPF", 51.51136375456851, -0.1160992115941371],
    "BI": ["Barbraham Institute - Animal Facility", "SPF", 52.13263404504375, 0.20565736818851812], #Cambridge
    "MUBSF": ["Manchester University-Biological Services Facility", "SPF", 53.46738462421384, -2.2335724269882755],
    "PI": ["Pirbright Institute-Brooksby Building", "SPF",  51.28058496691538, -0.6347443656236772],
}

#    
schemaDict = {
    "id": "https://nmgn.mrc.ukri.org/clusters/microbiome/",
    "name": "NMGN",
    "description": "A description of the schema containing one or more templates.",
    "version": "1.0.0",
    "in_language": ["en"],
    "imports": [
        "linkml:types"
    ],
    "prefixes": {
        "linkml": "https://w3id.org/linkml/",
        "GENEPIO": "http://purl.obolibrary.org/obo/GENEPIO_"
    },
    "classes": {
        "dh_interface": {
            "name": "dh_interface",
            "description": "A DataHarmonizer interface",
            "from_schema": "https://example.com/NMGN"
        },
        "NMGN_microbiome": {
            "name": "NMGN_microbiome",
            "title": "NMGN microbiome",
            "description": "National Mouse Genetics Network metadata template",
            "is_a": "dh_interface",
            "see_also": "templates/NMGN/SOP.pdf",
            "slots": 
                [], #lists name of all metadata fields. Inherit from field_name
            "slot_usage": {} #read field_name as key and index+1 as rank, and category as slot_group
        } 
    }, #end of 
    "slots": {}, #reads in information about each field (slot), each field has a different sub dictionary of name, title, description, comments, example 
    "enums": {
        "null value menu": {
            "name": "null value menu",
            "title": "null value menu",
            "description": "A menu of data collection status options for this field.",
            "permissible_values": {
                "Not Applicable": {
                    "text": "Not Applicable",
                    "meaning": "GENEPIO:0001619"
                },
                "Missing": {
                    "text": "Missing",
                    "meaning": "GENEPIO:0001618"
                },
                "Not Collected": {
                    "text": "Not Collected",
                    "meaning": "GENEPIO:0001620"
                },
                "Not Provided": {
                    "text": "Not Provided",
                    "meaning": "GENEPIO:0001668"
                },
                "Restricted Access": {
                    "text": "Restricted Access",
                    "meaning": "GENEPIO:0001810"
                }
            }
        },
        "host_sex_options":{
            "name": "host_sex_options",
            "title": "host_sex_options",
            "description": "gender or sex of the host",
            "permissible_values": {
                "male": {"text": "male"},
                "female": {"text": "female"},
                "missing data sample" : {"text": "missing data sample"}}
            },
        "Permitted_countries_menu": {
            'name': 'Permitted_countries_menu',
            'title': 'Permitted_countries_menu',
            'description': 'A list of permitted countires accepted by ENA',
            'permissible_values':{}
            },
        "Permitted_Facilities_menu":{
            "name": "Permitted_Facilities_menu",
            "title": "Permitted_Facilities_menu",
            "description": "A list of institutes-facilities (18) used by the NMGN microbiome cluster for mouse studies",
            "permissible_values":{ #TO UPDATE: list of 18 SPF facilities used by the NMGN.
                "MRC Harwell-Mary Lyons Centre":{"text": "MRC Harwell-Mary Lyons Centre"},
                "Francis Crick Institute-aimal facility":{"text":"Francis Crick Institute-aimal facility"},
                "Wellcome Sanger Institute-animal facility":{"text": "Wellcome Sanger Institute-animal facility"},
                "UE Queen's Medical Research Institute-Centre for Cardiovascular Science":{"text":"UE Queen's Medical Research Institute-Centre for Cardiovascular Science"},
                "Oxford Biomedial Services Building":{"text":"Oxford Biomedial Services Building"},
                "Cambridge University Biomedical Services":{"text":"Cambridge University Biomedical Services"},
                "King's College London-Animal Research Facility":{"text":"King's College London-Animal Research Facility"},
                "Barbraham Institute - Animal Facility":{"text":"Barbraham Institute - Animal Facility"},
                "Manchester University-Biological Services Facility":{"text":"Manchester University-Biological Services Facility"},
                "Pirbright Institute-Brooksby Building":{"text":"Pirbright Institute-Brooksby Building"}
                }
            },
        "cage_manufacturer_menu": {
            "name": "cage_manufacturer_menu",
            "title": "cage_manufacturer_menu",
            "description": "a list of manufacturers that the mouse cages are sourced from.",
            "permissible_values": {
                "Tecniplast": {"text": "Tecniplast"},
                "Allen town": {"text": "Allen town"},
                "NKP": {"text": "NKP"},
                "cage_manufacturer_4": {"text": "cage_manufacturer_4"},                
            }
        },
        "sample collection date precision menu": {
            "name": "sample collection date precision menu",
            "title": "sample collection date precision menu",
            "description": "date the sample was collected",
            "permissible_values" :{
                "year": {"text": "year", "meaning": "UO:0000036"},
                "month": {"text": "month", "meaning": "UO:0000035"},
                "day": {"text": "day", "meaning": "UO:0000033"},
            }
        },

        "nutrition_diet_types_option":{
            "name": "nutrition_diet_types_option",
            "title": "nutrition_diet_types_option",
            "description": "a list of diet types that can be provided to the NMGN mice.",
            "permissible_values":{
                "natural ingredients": {"text": "natural ingredients"},
                "chemically-defined": {"text": "chemically-defined"},
                "purified diet": {"text": "purified diet"},
                "transgenic mouse special food": {"text": "transgenic mouse special food"},
            }
        },
        "tax_id_menu": {
            "name": "tax_id_menu",
            "title": "tax_id_menu",
            "description": "Taxonomic identification of the organism(s) collected as in the NCBI Taxonomy database",
            "permissible_values": { # reflect mouse gut metagenome etc when going through the permissible values
                '410661' : {"text": "410661", "meaning": 'NCBITaxon:410661' #mouse gut metagenome
                            },
                '1441287' : {"text": "1441287", "meaning":'NCBITaxon:1441287' #mouse metagenome
                             }
                }
            },
        
    }, # end of enums section
    "types": {
        "WhitespaceMinimizedString": {
            "name": "WhitespaceMinimizedString",
            "typeof": "string",
            "description": "A string that has all whitespace trimmed off of beginning and end, and all internal whitespace segments reduced to single spaces. Whitespace includes #x9 (tab), #xA (linefeed), and #xD (carriage return).",
            "base": "str",
            "uri": "xsd:token"
        },
        "Provenance": {
            "name": "Provenance",
            "typeof": "string",
            "description": "A field containing a DataHarmonizer versioning marker. It is issued by DataHarmonizer when validation is applied to a given row of data.",
            "base": "str",
            "uri": "xsd:token"
        }
    }, #end of enums dict
    "settings": {
        "Title_Case": "(((?<=\b)[^a-z\W]\w*?|[\W])+)",
        "UPPER_CASE": "[A-Z\W\d_]*",
        "lower_case": "[a-z\W\d_]*"
    } #additional settings
}


#reads metadata into the existing schemaDict to create a schema.yaml file
def metadata2dict(metadata_file, schemadict):
    
    
    required_dict = {"mandatory": True,
                     "optional": False,
                     "recommended": False}
    
    metadata_df = pd.read_csv(metadata_file, delimiter="\t", na_values="na", keep_default_na="na", encoding='ISO-8859-1')

    #assign field_names to schemadict['classes']['NMGN']['slots'] as list
    schemadict['classes']['NMGN_microbiome']['slots'] = list(metadata_df['field_name'])#[:3]
    
    
    for i, (category, name, range_option, requirement, description, comment, example, uri, exact_maps) in enumerate(zip(list(metadata_df['category']), list(metadata_df['field_name']),list(metadata_df['range_options']), list(metadata_df['requirement']), list(metadata_df['description']), list(metadata_df['comments']), list(metadata_df['examples']), list(metadata_df['field_uri']), list(metadata_df['exact_mappings']))):    
    
        #read field_name as key and index+1 as rank, and category as slot_group
        rank = i+1

        #maps to the corresponding field for the template in export.js
        exact_mappings = exact_maps.split(";")
        
        #replace spaces with %20
        exact_mappings = [field.replace(" ", "%20") for field in exact_mappings]
        
        # print (exact_mappings[0].split(":")[-1])
        
        
        schemadict['classes']['NMGN_microbiome']['slot_usage'][name] = {'rank' : rank, 'slot_group' :category}
        
        schemadict['slots'][name] = {
            "name" : name, #name and title are the same
            "title": name,
            "description": description,
            "comments": (comment), #guidance
            "examples": [{"value" : example}],
            "slot_uri": uri,
            "range": "WhitespaceMinimizedString",
            # "required": required,
            # "recommended": recommended,
            "exact_mappings": exact_mappings, #need to find the correct URI or CURIE for ENA sample registration (ENA_sample_registration:sample collection method is not a valid URI or CURIE)
            # "structured_pattern": {} #for controlled text - "structured_pattern": {"syntax": "{UPPER_CASE}", "partial_match": False, "interpolated": True}
            }
        
        #add mandatory or recommended options
        if requirement == "mandatory":
            schemadict['slots'][name]["required"] = True
        
        elif requirement == "optional":
            schemadict['slots'][name]["recommended"] = True

        else:
            schemadict['slots'][name]["required"] = False
        
        #if range_option is not null, add to range
        if str(range_option) != 'nan':
            schemadict['slots'][name]["range"] = range_option #Menu selection (under columns)
            
            schemadict['slots'][name]["range"] = range_option #Menu selection (under columns)
            

            # if ';' in range_option: ´#option to add any_of does not work yet. Need to fix
            #     options_list = range_option.split(';')
            #     schemadict['slots'][name]["any_of"] = [" : ".join(["range", option]) for option in options_list]
            # else:
                # schemadict['slots'][name]["range"] = range_option
        # if i == 2:
        #     break
        
    return schemadict

#parse metadata dict into yaml format
def dict2yaml(schema_dict, yaml_filepath):

    with open(yaml_filepath, 'w') as file:
        yaml.dump(schemaDict, file, default_flow_style=False, sort_keys=False)    

    # print (yaml_filepath)

    return ""

#get ontology from country name
def get_onto_from_name(country):

    # Define the API URL
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={country}"
    
    # Send a GET request to the API
    response = requests.get(url)
    
    # Parse the response JSON into a Python dictionary
    angola_ontology = response.json()
    
    #get the GAZ ID
    GAZ_ID = angola_ontology['response']['docs'][-1]['obo_id']
    
    #print (country, GAZ_ID)

    return GAZ_ID

#read variables from metadata file and read into Dicts for creating export.js file
def metadata2jsDict(metadata_file):

    metadata_df = pd.read_csv(metadata_file, delimiter="\t", na_values="", keep_default_na="na", encoding='ISO-8859-1')

    #read metadata to dict
    headers_dict = {field: [] for field in metadata_df['field_name']}

    unitsDict = metadata_df.set_index('field_name')['units'].to_dict() 

    #reformat unitsDict
    unitsDict = {k: [v] if isinstance(v, (str, list, tuple, set, dict)) and len(v) > 0 else [] for k, v in unitsDict.items()}

    #print (unitsDict)

    return headers_dict, unitsDict


def generate_json(headersDict, unitsDict, export_js_file):

    file_type = 'tsv'
    status = 'published'

    checklist_dict = {
        'Checklist': [],
        'ERC000013': [],
        'GSC MIxS host associated': []
    }



    js_template = '''// A dictionary of possible export formats
    export default {{
        /**
        * Download secondary headers and grid data.
        * @param {{Object}} dh DataHarmonizer instance.
        */

        // Biosample seq tsv format
        ENA_host_associated: {{
        fileType: '{file_type}',
        status: '{status}',
        method: function (dh) {{
            // Create Checklist Header for ENA file
            const ExportChecklist = new Map([
    {checklist_entries}
            ]);
            
            // Create an export table with template's headers (2nd row) and remaining rows of data
            const ExportHeaders = new Map([
    {header_entries}
            ]);

            // Create #units Header for ENA file
            const ExportUnits = new Map([
    {unit_entries}
            ]);
        
            const sourceFields = dh.getFields(dh.table);
            const sourceFieldNameMap = dh.getFieldNameMap(sourceFields);
            // Fills in the above mapping (or just set manually above)
            dh.getHeaderMap(ExportHeaders, sourceFields, 'ENA');

            // Copy headers to 1st 3 rows of new export table
            const outputMatrix = [[...ExportChecklist.keys()],
                [...ExportHeaders.keys()],
                [...ExportUnits.values()],
            ];

            for (const inputRow of dh.getTrimmedData(dh.hot)) {{
                const outputRow = [];
                for (const [headerName, sources] of ExportHeaders) {{
                    // Otherwise apply source (many to one) to target field transform:
                    const value = dh.getMappedField(
                        headerName,
                        inputRow,
                        sources,
                        sourceFields,
                        sourceFieldNameMap,
                        ':',
                        'ENA'
                    );
                    outputRow.push(value);
                }}
                outputMatrix.push(outputRow);
            }}
            return outputMatrix;
        }},
        }},
    }};
    '''

    # Convert Python dictionary to JS Map format
    checklist_entries = "".join(f"          ['{key}', {value}],\n" for key, value in checklist_dict.items())
    header_entries = "".join(
        f"          ['{key}', {value}],\n" for key, value in headersDict.items()
    )

    unit_entries = "".join(
        f"          ['{key}', {value}],\n" for key, value in unitsDict.items()
    )

    # Generate JavaScript content
    js_content = js_template.format(checklist_entries=checklist_entries, header_entries=header_entries, 
                                    unit_entries=unit_entries, file_type=file_type, status=status
                                    )

    # Save to a JavaScript file
    output_file = "generated_export.js"
    with open(export_js_file, "w", encoding="utf-8") as file:
        file.write(js_content)


    return ""

def main():
    parser = argparse.ArgumentParser(
        prog = "dataharmonizer-support",
        usage = "dataharmonizer-support.py --input_tsv <input_tsv_file> --result_directory <result_directory>",
        description = "The dataharmonizer-support script is designed to generate the primary json and yaml files that the DataHarmonizer "
        "program needs to generate templates for harmonizing data to a specific format. Harmonized data can then be used to submit data to """
        "specific data archived.",
epilog = "The export.js and schema.yaml files generated by dataharmonizer-support can be used directly by dataharmonizer to generate templates for entering and harmonizing the data."
    )
    parser.add_argument(
        "--input_tsv", "-i",
        help="input tsv file with all relavent information for generating both the schema.yaml or export.js file",
        default=None,
        required=True
    )
    parser.add_argument(
        "--result_directory", "-r",
        help="directory to store generated schema.yaml and export.js files.",
        default="result_directory",
        required=False
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    #assign variables
    input_tsv = args.input_tsv
    result_directory = args.result_directory

    
    result_schema_file = os.path.join(result_directory, "schema.yaml") #result yaml file
    result_export_file = os.path.join(result_directory, "export.js")

    country_genpio_file = os.path.join("metadata_files", "countries_gaz2.tsv")


    #read country_genpio file into dict - schemaDict['enums']['Permitted_countries']
    country_dict = pd.read_csv(country_genpio_file, delimiter="\t", na_values="na", keep_default_na="na", encoding='ISO-8859-1').set_index('Country')['GENPIO'].to_dict()
    schemaDict['enums']['Permitted_countries_menu']['permissible_values'] = {country:{'text':country} for country in country_dict}

    #read metadatafile and update schemaDict2
    schemaDict2 = metadata2dict(input_tsv, schemaDict)

    #convert schemaDict2 into schema.yaml file
    dict2yaml(schemaDict2, result_schema_file)

    #convert jsDict and generate export.js file
    header_dict, unitsDict = metadata2jsDict(input_tsv)
    generate_json(header_dict, unitsDict, result_export_file)


if __name__ == "__main__":
    main()
    


    




