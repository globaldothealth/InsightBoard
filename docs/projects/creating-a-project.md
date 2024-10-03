# Creating a project

Briefly, you will need to provide: 1) a target schema for the data you want to ingest, 2) parsers to ingest data from various formats, and 3) reports to generate summaries of the data.

```bash
├─ parsers/
│  ├─ parser_1.py            # Parsers to ingest data from various formats
│  └─ ...
├─ reports/
│  ├─ report_1.py            # Sample report to generate a summary of the data
│  └─ ...
└─ schemas/
   ├─ target.schema.json     # JSON schema for the 'target' table
   └─ ...
```

The sample project provides examples of each of these files. In-fact, it may be simpler to use the sample project as a template when constructing a new project. Navigate to [InsightBoard-SampleProject](https://github.com/globaldothealth/InsightBoard-SampleProject) and click on the `Use this template` button to create a new repository with the same structure, then `git clone <your-repo-url> <your-repo-name>` to the `InsightBoard\projects` directory. Once the project is created, you can modify the files to suit your needs - see below for details of each component.

## Components

```{toctree}
---
maxdepth: 2
---
components/schemas
components/parsers
components/reports
```
