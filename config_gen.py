import streamlit as st
import json

# Define available transformations and their parameter requirements
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

def get_parameter_value(param_type, label, options, key, columns=None):
    """Get parameter value based on type"""
    if param_type == "multiselect":
        return st.multiselect(label, options=columns if columns else options, key=key)
    elif param_type == "select":
        return st.selectbox(label, options=options if options else columns, key=key)
    elif param_type == "text":
        return st.text_input(label, key=key)
    return None

def create_transformation_form(index, columns):
    """Create a form section for a single transformation"""
    st.subheader(f"Transformation {index + 1}")
    
    # Action selection for this transformation
    action = st.selectbox(
        "Action Type",
        options=list(TRANSFORMATION_ACTIONS.keys()),
        format_func=lambda x: TRANSFORMATION_ACTIONS[x]["display_name"],
        key=f"action_type_{index}"
    )
    
    # Get the parameters for this action
    action_params = TRANSFORMATION_ACTIONS[action]["parameters"]
    parameters = {}
    
    # Create inputs for each parameter
    for param_name, param_config in action_params.items():
        param_type = param_config["type"]
        param_label = param_config["label"]
        param_options = param_config.get("options", None)
        param_key = f"{action}_{param_name}_{index}"
        
        value = get_parameter_value(param_type, param_label, param_options, param_key, columns)
        if value is not None:
            parameters[param_name] = value
    
    return {
        "action": action,
        "parameters": parameters
    }

def create_config_form():
    st.title("WMS File Parsing Configuration")
    
    with st.form("config_form"):
        # File Configuration Section
        st.subheader("File Configuration")
        file_type = st.selectbox("File Type", ["file", "zip", "gz"], key="file_type")
        file_format = st.selectbox("File Format", ["csv", "xls", "xlsx"], key="file_format")
        encoding = st.selectbox("Encoding", ["utf-8", "ascii", "iso-8859-1"], key="encoding")
        delimiter = st.selectbox("Delimiter", [",", "|", ":", "\t"], key="delimiter")
        skip_rows = st.number_input("Skip Rows", min_value=0, value=0, key="skip_rows")
        
        # Column Names Input Section
        st.subheader("Column Names")
        columns_input = st.text_area(
            "Enter column names (one per line)",
            height=100,
            help="Enter each column name on a new line"
        )
        
        # Convert input text to list of columns
        columns = [col.strip() for col in columns_input.split('\n') if col.strip()]
        
        if columns:
            st.write(f"Number of columns detected: {len(columns)}")
            
            # Transformations Section
            st.subheader("Transformations")
            num_transformations = st.number_input(
                "Number of Transformations",
                min_value=1,
                max_value=10,
                value=1,
                key="num_transformations"
            )
            
            # Create forms for each transformation
            transformations = []
            for i in range(num_transformations):
                transformation = create_transformation_form(i, columns)
                transformations.append(transformation)
                if i < num_transformations - 1:
                    st.markdown("---")
        else:
            st.warning("Please enter column names to configure transformations.")
            transformations = []
        
        submitted = st.form_submit_button("Generate Configuration")
        
        if submitted and columns:
            # Clean up the transformations to remove empty values and ensure proper format
            cleaned_transformations = []
            for t in transformations:
                # Remove any empty or None values from parameters
                cleaned_params = {k: v for k, v in t["parameters"].items() if v is not None and v != []}
                if cleaned_params:
                    cleaned_transformations.append({
                        "action": t["action"],
                        "parameters": cleaned_params
                    })
            
            config = {
                "type": "wms-file-parsing",
                "config": {
                    "file_type": file_type,
                    "file_format": file_format,
                    "encoding": encoding,
                    "delimiter": delimiter,
                    "skip_rows": skip_rows,
                    "transformations": cleaned_transformations
                }
            }
            
            # Display the generated configuration
            st.subheader("Generated Configuration")
            st.json(json.dumps(config, indent=2))
            
            # Provide download option
            st.download_button(
                label="Download Configuration",
                data=json.dumps(config, indent=2),
                file_name="wms_config.json",
                mime="application/json"
            )

if __name__ == "__main__":
    create_config_form()
