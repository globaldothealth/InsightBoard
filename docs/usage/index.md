# Usage

**Insight**Board is a tool for creating and sharing interactive dashboards. It is designed to be easy to use and flexible, so you can create dashboards that meet your specific needs. For more information about projects, including how to create and manage them, see the [projects](../projects/index.md) page.

## Sample project

### Homepage

**Insight**Board comes with a sample project that demonstrates how to use the dashboard. Make sure you have installed **Insight**Board and the sample project according to the setup instructions, then launch the dashboard. You should see `sample_project` in the list of available projects in the upper-left corner. If not, please refer back to the installation instructions and ensure the project is located in the correct folder so that **Insight**Board can find it. Click on the project to open it.

![Home](images/home.png)

You can now choose to `Upload` data into the project database, view `Data` in the database, run `Reports` on the database, or create a parser for a `New Dataset`. Since the sample project is empty, let's start by uploading some data. Click on `Upload` to open the upload screen.

### Upload data

The upload screen will prompt you to select a parser and a data file to ingest. The sample project comes with an `adtl` parser named `adtl-source1` and a sample data file called `sample_data_source1.csv` (located in the `sample_project/data` folder). Select the `adtl-source1` parser and the `sample_data_source1.csv` file, then click `Upload`.

![Upload](images/upload.png)

The data source should convert from its native format to the target schema (these have been setup as a demonstration), but there will be some fields that do not comply with the target schema. These are highlighted in red in the datatable so that you can assess whether they need to be corrected. Hovering over the field will provide a description of the validation error so that you can make the necessary changes. Try correcting some of the fields and selecting `Revalidate` (just below the DataTable) to re-check the data.

![datatable](images/datatable.png)

A validation report also appears just below the table (scroll down to see it) which, by default, only shows errors for the visible portion of the table. This is useful for cross-referencing the errors with the data in the table. You can also switch the `Show full validation log` button to see all errors in the dataset.

![validate](images/validate.png)

After making some changes and revalidating, click `Commit to database` to add the data to the database. Note that you do not have to address _all_ of the changes if you need to input data quickly. A dataset will typically employ a 'PrimaryKey' (a unique identifier for an individual, for example), that will allow you to update records later as more information becomes available. When you click `Commit to database` you will be prompted with a list of tables that you are importing (the parser supports multiple table imports), through there is only one to check in this case. Click `Ok` to proceed.

### Data

On the data page you will be presented with a list of tables available in the database. When you first open the `sample_project` this list will be empty, but it will popualate as soon as you add data through the `upload` page. Click on the table you just imported to browse through the data. You will notice that any changes you applied to the data during the upload process are reflected in the database.

![data](images/data.png)

### Reports

Reports provide a powerful tool to interrogate the data in the database. Reports are pre-configured using templates for more information). For now we have provided a sample report called `summary` that provides a brief summary of the data in the database, along with a few visualizations. Click on the `summary` report to generate the report. This can take some time with larger databases as the reports are generated on the most up-to-date data.

![reports](images/reports.png)

### New Dataset

Within the sample project, there are 2 'sample data' datasets. `sample_data_source1.csv` has a parser already provided, and it's use has been demonstrated above.
`sample_data_source2.csv` does not, and is provided for you to try out the automated parser generation tooling, which uses LLMs.

From the `Home` page or the using the navigation bar, select `New Dataset`. The screen will prompt you to select which LLM you wish to use, provide an API key for that model, choose the language the data is in, and upload the data. Select `sample_data_source2.csv` as your data this time, as we don't have a parser for that data yet. The first stage of this process is to create a 'data dictionary' which describes the properties of the dataset. An LLM can be used to auto-fill the 'description' column of the dictionary; if you would rather fill these in by hand you can toggle off the `Generate descriptions with LLM` option.


Once these have been filled in, select `Create Dictionary`.

![make-dict](images/new-parser-make-dict.png)

A dictionary will now be displayed, showing the column names from `sample_data_source2.csv` as well as a description of what the column contains (which will be an English translation if non-english data is provided), the type of data in each column, and a set of `Common Values`. This is filled in with any entries deemed to be frequently occuring in the column, based on a value set in the config file, and the length of the dataset.

At this point you should check that all the columns have been accurately described, and that there is **no identifying information** in the `Common Values` column. The LLM will be shown this data dictionary in the next step, so identifying information such as names, address etc should not be present.

When you are satisfied that the dictionary is correct, select the `Create Mapping` button.

![make-map](images/new-parser-make-map.png)

The displayed table will now update to show mappings between the fields in the source dataset (`sample_data_source2.csv`) and the required fields from the target schema, along with mappings for any required terminology (listed as enum values in the schema). Both the field and value mapping have been generated by an LLM; while usually reasonably accurate they can make mistakes, so you should **check that both the field and values mappings** (scroll to the end of the table to see these) **are accurate**. As with the `Upload` screen, the data can be edited in the window.

Once you are happy, create a name for the new parser and select the `Generate Parser` button. This will save a new parser to your `sample_project` folder, ready to be used in the [`Upload` screen](#upload-data).

![make-toml](images/new-parser-make-toml.png)
