import pandas as pd
import matplotlib.pyplot as plt
from utils.database_singleton import db
import utils.values as values
import os 



async def process_excel(path):
    exceptions = []
    df = pd.read_excel(path)
    unique_names = df['name'].unique()
    projects_table = "projects"
    unique_names_df = pd.DataFrame({'name': unique_names})
    #err = await db.add_rows(unique_names_df, projects_table, "name", "name")
    err = await db.add_rows(unique_names_df, projects_table)
    if err: 
        exceptions.append(err)
    merged_df, err  = await provide_id_to_data(df)
    if err: 
        exceptions.append(err)
    data_table = "project_data"
    err = await db.add_rows(merged_df, data_table)
    if err: 
        exceptions.append(err)
    return exceptions

async def provide_id_to_data(excel_data):
    data, columns, err = await db.simple_select_query("projects")
    if err:
        return None, err
    project_names_df = pd.DataFrame(data, columns=columns)
    merged_df = pd.merge(project_names_df, excel_data, left_on='name', right_on='name', how='left')
    merged_df = merged_df.drop(columns=['name'])
    merged_df = merged_df.rename(columns={'id': 'project_id'})
    return merged_df, None

async def db_to_df():
    projects_data, projects_columns, err = await db.simple_select_query("projects")
    if err:
        return None, err
    project_data_data, project_data_columns, err = await db.simple_select_query("project_data")
    if err:
        return None, err
    projects_df = pd.DataFrame(projects_data, columns=projects_columns)
    project_data_df = pd.DataFrame(project_data_data, columns=project_data_columns)

    if projects_df.empty or project_data_df.empty:
        return None, None
    merged_df = pd.merge(projects_df, project_data_df, left_on='id', right_on='project_id')
    merged_df = merged_df.drop(columns=['id'])
    return merged_df, None


async def plot_data(df, path):
    if not isinstance(df, pd.DataFrame):
        return None, "Error: Provided data is not a DataFrame"
    if 'name' not in df.columns or 'year' not in df.columns or 'cost' not in df.columns:
        return None, "Error: Missing required columns in DataFrame"
    plt.figure(figsize=(10, 6))
    for name, group in df.groupby('name'):
        plt.plot(group['year'], group['cost'], marker='o', label=name)
    plt.title('Cost vs. Year')
    plt.xlabel('Year')
    plt.ylabel('Cost')
    plt.legend(title='Name')
    plt.grid(True)
    unique_filename = f"{values.timestamp}_{values.random_chars}_plot.png"
    plt.savefig(os.path.join(path, unique_filename))
    plt.close()

    return os.path.join(path, unique_filename), None
