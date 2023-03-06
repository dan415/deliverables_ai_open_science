<h1>Assumptions</h1>

- Grobid must be running at the time of execution
- Grobid's config file provided to the program must exist, when running from source
- provided input_files folder must exist, when running from source
- provided output_files folder must exist, when running from source

<h1>Algorithm</h1>

This program will try to process all PDF files stored in given input files folder and produce:
- A grobid-generated TEI xml for each of the files
- A links.txt file in json format with a list of encountered links for each of the files
- wordcloud.png A wordcloud image, generated with the concatenated text of all abstracts in the files
- figures.png A bar plot summarizing the count of figures found in each file

<h1>Usage</h1>

    usage: PDF Analysis [-h] [--INPUT_PATH INPUT_PATH] [--OUTPUT_PATH OUTPUT_PATH] [--GROBID_CLIENT_CONFIG_PATH GROBID_CLIENT_CONFIG_PATH]
    
    Analyse PDFs using GROBID
    
    options:
    
      -h, --help            show this help message and exit
    
      --INPUT_PATH INPUT_PATH
    
    Path to the input directory containing the PDFs to be analysed

      --OUTPUT_PATH OUTPUT_PATH --OUTPUT_PATH OUTPUT_PATH

    Path to the output directory where the results will be stored
    
      --GROBID_CLIENT_CONFIG_PATH GROBID_CLIENT_CONFIG_PATH 
      
    Path to the GROBID client configuration file


<h1>Objectives of this program</h1>

1. Draw a keyword cloud based on the abstract information
2. Create a visualization showing the number of figures per article.
3. Create a list of the links found in each paper.

All outputs are saved in defined output folder

<h2>Objective 1</h2>
For objective 1, library wordcloud is used. For more precise results, stopwords are identified and eliminated from the text.

The langauge for the set of stop words to use are obtained from the *lang attribute* from the *TEI header*.

Stop word removal will not be used if unable to identify said attribute or language code is not one of acccepted langauges.

Accepted langauges are:
- spanish
- english
- german
- french
- portuguese
- italian

The wordcloud is stored as a PNG file.

<h2>Objective 2</h2>

For objective 2, the way figures are identified is by searching for the tag *figure* in the xml tree structure. 

The counts are obtained and then plotted with *matplotlib*

<h2>Objective 3</h2>

For objective 3, links are identified in two ways. For DOI's present in the file, the generated *ptr* tags are used to retrieve
the links. Next, Using the text of the PDF file, a regex expression is used to find link-formatted text.
