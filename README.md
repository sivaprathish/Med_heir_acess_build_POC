# Relationship tab update

Copy app.py and relationship_actions.py into your existing hierarchy_poc folder. Replace app.py. Keep your current core.py and data folder unchanged. Restart Streamlit with `python -m streamlit run app.py`.

- Add: parent, child and start date only. Generates a new ID, leaves end blank.
- Modify: select an open-ended relationship, select a different parent and effective date. Keeps the old ID and sets its end date; inserts a new ID for the same child with the same effective start date and a blank end. Both changes are validated and saved in the same CSV write.
- End: select an open-ended relationship and end date. Keeps its ID and adds no row.

The existing node_relationships.csv columns are unchanged. No CSV files are included, so your current data is preserved. The helper imports validate and next_id from your existing core.py. Other screens are unchanged.

Dates remain YYYY-MM-DD, not timestamps. End dates are exclusive. Modify/End dates must be later than the selected row's start date. Same-day changes require timestamp support, which this update does not add. Closed/scheduled-to-end rows cannot be edited through these actions. They remain visible in the history table. Modifying means changing the parent of the selected child; use Add for an unrelated new child.

Validation checks run before saving. Invalid changes do not mutate the original data. Local single-user use only. The selected new parent still needs a valid path to root for reporting; existing reporting completeness warnings continue to apply.

Run the focused tests from your project folder:
`python -m unittest -v test_relationship_actions`
