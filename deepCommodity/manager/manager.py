from google.cloud import bigquery
import matplotlib.pyplot as plt

class Manager():

    def __init__(self):
        pass

    @staticmethod
    def plot_history(history):

        fig, ax = plt.subplots(1, 2, figsize=(20, 7))
        # --- LOSS: MSE ---
        ax[0].plot(history.history['loss'])
        ax[0].plot(history.history['val_loss'])
        ax[0].set_title('MSE')
        ax[0].set_ylabel('Loss')
        ax[0].set_xlabel('Epoch')
        ax[0].legend(['Train', 'Validation'], loc='best')
        ax[0].grid(axis="x", linewidth=0.5)
        ax[0].grid(axis="y", linewidth=0.5)

        # --- METRICS:MAE ---

        ax[1].plot(history.history['mae'])
        ax[1].plot(history.history['val_mae'])
        ax[1].set_title('MAE')
        ax[1].set_ylabel('MAE')
        ax[1].set_xlabel('Epoch')
        ax[1].legend(['Train', 'Validation'], loc='best')
        ax[1].grid(axis="x", linewidth=0.5)
        ax[1].grid(axis="y", linewidth=0.5)

        return ax

    @staticmethod
    def upload_dataframe_to_bigquery(df, bq_table):
        # Initialize BigQuery client and dataset
        client = bigquery.Client()
        dataset_ref = client.dataset(bq_table.dataset_id)

        # Check if dataset exists, and create it if not
        try:
            client.get_dataset(dataset_ref)
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            client.create_dataset(dataset)

        # Create BigQuery table schema
        schema = []
        for col in df.columns:
            if df.dtypes[col] == 'int64':
                field_type = 'INTEGER'
            elif df.dtypes[col] == 'float64':
                field_type = 'FLOAT'
            elif df.dtypes[col] == 'bool':
                field_type = 'BOOLEAN'
            else:
                field_type = 'STRING'
            schema.append(bigquery.SchemaField(col, field_type))

        # Create BigQuery table reference
        table_ref = dataset_ref.table(bq_table.table_id)

        # Check if table exists, and create it if not
        try:
            client.get_table(table_ref)
        except NotFound:
            table = bigquery.Table(table_ref, schema=schema)
            client.create_table(table)

        # Load data into BigQuery table without repeating rows
        job_config = bigquery.LoadJobConfig(write_disposition='WRITE_APPEND')
        job = client.load_table_from_dataframe(df,
                                            table_ref,
                                            job_config=job_config)
        job.result()
