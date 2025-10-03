import streamlit as st
import pandas as pd
import io
from io import BytesIO

def transpose_row(row, headers):
    """Transpose a single row into multiple rows"""
    transposed_rows = []
    
    # Fixed values that stay the same for all transposed rows
    fixed_columns = headers[:11]  # journal to Adjusted activity
    fixed_values = row[:11]
    
    # Activity columns start from index 11 (Balance) onwards
    activity_headers = headers[11:]
    activity_values = row[11:]
    
    for i, (activity_header, value) in enumerate(zip(activity_headers, activity_values)):
        # Skip if value is missing (represented as '-', empty, or NaN)
        if (isinstance(value, str) and value.strip() in ['-', '']) or pd.isna(value):
            continue
            
        # Create new row: fixed values + activity header + value
        new_row = fixed_values + [activity_header, value]
        transposed_rows.append(new_row)
    
    return transposed_rows

def to_excel(df):
    """Convert dataframe to Excel format"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transformed_Data')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title("Data Transformer")
    st.write("Upload your file to transpose the data")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'txt', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            # Read file based on extension
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file, delimiter='\t')
            
            st.write("Original Data:")
            st.dataframe(df)
            
            # Get headers
            headers = df.columns.tolist()
            
            # Process data
            all_transposed_rows = []
            
            for _, row in df.iterrows():
                transposed_rows = transpose_row(row.tolist(), headers)
                all_transposed_rows.extend(transposed_rows)
            
            # Create new dataframe
            if all_transposed_rows:
                new_headers = headers[:11] + ['Activity', 'Amount']
                new_df = pd.DataFrame(all_transposed_rows, columns=new_headers)
                
                st.write("Transformed Data:")
                st.dataframe(new_df)
                
                # Create two columns for download buttons
                col1, col2 = st.columns(2)
                
                # CSV Download button
                with col1:
                    csv = new_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="transformed_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                # Excel Download button
                with col2:
                    excel_data = to_excel(new_df)
                    st.download_button(
                        label="📊 Download as Excel",
                        data=excel_data,
                        file_name="transformed_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                # Show some stats
                st.success(f"✅ Transformation complete! Created {len(new_df)} rows from original data.")
                
            else:
                st.warning("No valid data found to transform")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("💡 Tip: Make sure your file has the correct format with tab delimiter for CSV/TXT files.")

if __name__ == "__main__":
    main()
