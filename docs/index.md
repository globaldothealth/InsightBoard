# **Insight**Board

InsightBoard is a powerful tool for ingesting and reporting on data from multiple sources. The app allows you to seamlessly transform various data formats into a unified schema, store them in a central database, and generate custom reports, including interactive visualizations.

## Key Features

- Data Ingestion: Import data from multiple sources using custom parsers.
- Schema Normalization: Homogenize incoming data to a target schema.
- Centralized Database: Store all ingested data in a central repository for easy access and analysis.
- Custom Reporting: Create personalized reports with filters, aggregations, and visual representations of the data.
- Data Visualization: Generate charts, graphs, and other visuals directly from the ingested datasets.

## Framework

<p style="text-align: center">

```{mermaid}
graph LR
    A1[Data source 1] --> B1[Parser 1]
    A2[Data source 2] --> B2[Parser 2]
    An[Data source n] --> Bn[Parser n]

    B1 --> C[Target schema]
    B2 --> C
    Bn --> C

    C --> D[Validation]
    D --> E[Database]

    E --> F1[Report 1]
    E --> F2[Report 2]
    E --> Fn[Report n]

    style A1 fill:#ffffff,stroke:#333,stroke-width:2px;
    style A2 fill:#ffffff,stroke:#333,stroke-width:2px;
    style An fill:#ffffff,stroke:#333,stroke-width:2px;
    style B1 fill:#ffffff,stroke:#333,stroke-width:2px;
    style B2 fill:#ffffff,stroke:#333,stroke-width:2px;
    style Bn fill:#ffffff,stroke:#333,stroke-width:2px;
    style C fill:#ffffff,stroke:#333,stroke-width:2px;
    style D fill:#ffffff,stroke:#333,stroke-width:2px;
    style E fill:#ffffff,stroke:#333,stroke-width:2px;
    style F1 fill:#ffffff,stroke:#333,stroke-width:2px;
    style F2 fill:#ffffff,stroke:#333,stroke-width:2px;
    style Fn fill:#ffffff,stroke:#333,stroke-width:2px;
```

</p>

## Sample report

```{figure} images/sample-report.png
Sample InsightBoard report showing summary statistics and interactive visualizations
```


## Documentation

```{toctree}
---
maxdepth: 2
---
self
getting_started/index
usage/index
projects/index
advanced/branding
```
