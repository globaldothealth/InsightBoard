# Schemas

The target schema is a JSON file that describes the structure of the data you want to ingest. It is used to validate the data and ensure that it is correctly formatted before being stored in the database.

A basic example schema is shown below:
```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "format": "string",
      "PrimaryKey": true
    },
    "date": {
      "type": "string",
      "format": "date"
    },
    "country": {
      "type": "string"
    },
    "value": {
      "type": "number"
    }
  },
  "required": ["id", "date", "country", "value"]
}
```

InsightBoard uses the standard JSON schema format, as described in [json-schema.org](https://json-schema.org/). The schema should be saved in the `schemas` folder of the project with the name `target.schema.json` (where 'target' can be substituted for the desired table name in the database).

The following schema extensions are supported by InsightBoard:
- `PrimaryKey`: A boolean value that specifies whether the field is a primary key in the database. This is important to ensure that the data is correctly indexed and that duplicates are not stored.
