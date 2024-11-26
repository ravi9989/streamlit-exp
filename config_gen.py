import streamlit as st
import pandas as pd
import json
import requests
import zipfile
import gzip
import io

# Transformation actions and their parameters
TRANSFORMATION_ACTIONS = {
    "select_columns": {
        "display_name": "Select Columns",
        "parameters": {
            "column_names": {
                "type": "multiselect",
                "label": "Select Columns"
            }
        }
    },
    "normalising_df_wrt_parent_column": {
        "display_name": "Normalize Parent-Child",
        "parameters": {
            "parent_column": {
                "type": "select",
                "label": "Parent Column"
            },
            "child_column": {
                "type": "select",
                "label": "Child Column"
            }
        }
    },
    "delete_columns": {
        "display_name": "Delete Columns",
        "parameters": {
            "column_names": {
                "type": "multiselect",
                "label": "Select Columns to Delete"
            }
        }
    },
    "filter_rows": {
        "display_name": "Filter Rows",
        "parameters": {
            "column": {
                "type": "select",
                "label": "Column"
            },
            "operator": {
                "type": "select",
                "label": "Operator",
                "options": ["equals", "not_equals", "greater_than", "less_than", "contains"]
            },
            "value": {
                "type": "text",
                "label": "Value"
            }
        }
    }
}

def main():
    # Streamlit app to configure WMS file details
    st.title("WMS File Configuration Tool")
    
    # Form fields for initial file configuration
    st.subheader("Initial File Configuration")
    file_type = st.selectbox("File Type", ["file", "zip", "gz"], index=0)
    file_format = st.selectbox("File Format", ["csv", "xls", "xlsx"], index=0)
    encoding = st.selectbox("Encoding", ["utf-8", "ascii", "iso-8859-1"])
    delimiter = st.selectbox("Delimiter", [",", "|", ":", "\t"], index=0)
    skip_rows = st.number_input("Skip Rows", value=0, min_value=0)
    
    # Upload CSV file
    uploaded_file = st.file_uploader("Upload a File", type=["csv", "xlsx", "zip", "gz"])
    df = None
    if uploaded_file is not None:
        try:
            # Read uploaded file based on given configurations
            if file_type == "file":
                if file_format == "csv":
                    df = pd.read_csv(uploaded_file, encoding=encoding, delimiter=delimiter, skiprows=skip_rows)
                elif file_format in ["xls", "xlsx"]:
                    df = pd.read_excel(uploaded_file, skiprows=skip_rows)
            elif file_type == "zip":
                with zipfile.ZipFile(uploaded_file) as z:
                    # Assuming there's only one file in the zip
                    file_name = z.namelist()[0]
                    with z.open(file_name) as f:
                        if file_format == "csv":
                            df = pd.read_csv(f, encoding=encoding, delimiter=delimiter, skiprows=skip_rows)
                        elif file_format in ["xls", "xlsx"]:
                            df = pd.read_excel(f, skiprows=skip_rows)
            elif file_type == "gz":
                with gzip.open(uploaded_file, 'rt', encoding=encoding) as f:
                    if file_format == "csv":
                        df = pd.read_csv(f, delimiter=delimiter, skiprows=skip_rows)
        
            # Display the dataframe preview
            st.write("Uploaded file preview:")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
        if df is not None:
            # Extract column names
            columns = df.columns.tolist()
            
            # Transformation Configuration
            st.subheader("Transformations")
            if "transformations" not in st.session_state:
                st.session_state["transformations"] = []
            
            action = st.selectbox("Select Transformation", list(TRANSFORMATION_ACTIONS.keys()), key="action_select")
            parameters = {}
            action_config = TRANSFORMATION_ACTIONS.get(action, {})
            for param, param_details in action_config.get("parameters", {}).items():
                param_type = param_details.get("type")
                if param_type == "multiselect":
                    parameters[param] = st.multiselect(param_details.get("label", param), columns, key=f"{action}_{param}")
                elif param_type == "select" and "options" in param_details:
                    parameters[param] = st.selectbox(param_details.get("label", param), param_details.get("options"), key=f"{action}_{param}")
                elif param_type == "select":
                    parameters[param] = st.selectbox(param_details.get("label", param), columns, key=f"{action}_{param}")
                elif param_type == "text":
                    parameters[param] = st.text_input(param_details.get("label", param), key=f"{action}_{param}")
                elif param_type == "number":
                    parameters[param] = st.number_input(param_details.get("label", param), min_value=0, key=f"{action}_{param}")
            
            if st.button("Add Transformation", key="add_transformation"):
                transformation = {"action": action, "parameters": parameters}
                st.session_state["transformations"].append(transformation)
            
            # Display current transformations
            st.write("Current Transformations:")
            for idx, t in enumerate(st.session_state["transformations"]):
                st.text(json.dumps(t, indent=2))
                if st.button(f"Delete Transformation {idx+1}", key=f"delete_transformation_{idx}"):
                    st.session_state["transformations"].pop(idx)
                    st.experimental_rerun()
            
            # Submit Configuration
            if st.button("Submit Configuration", key="submit_config"):
                config = {
                    "type": "wms-file-parsing",
                    "config": {
                        "file_type": file_type,
                        "file_format": file_format,
                        "encoding": encoding,
                        "delimiter": delimiter,
                        "skip_rows": skip_rows,
                        "transformations": st.session_state["transformations"]
                    }
                }
                # Display JSON configuration
                st.write("Generated Configuration JSON:")
                st.text(json.dumps(config, indent=2))
                
                # Optional: Send to Azure Function
                # azure_function_url = st.text_input("Azure Function URL")
                # if azure_function_url:
                #     response = requests.post(azure_function_url, json=config)
                #     st.write(f"Azure Function Response Status Code: {response.status_code}")
                #     if response.ok:
                #         st.success("Configuration successfully sent to Azure Function.")
                #     else:
                #         st.error("Failed to send configuration to Azure Function.")

if __name__ == "__main__":
    main()
