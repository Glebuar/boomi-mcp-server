"""
Boomi Process Shape Templates.

Individual shape templates extracted from real Boomi processes.
These templates represent the structure while builders handle the logic.
"""

# Start Shape Template
START_SHAPE_TEMPLATE = """        <shape image="start"
               name="{name}"
               shapetype="start"
               userlabel="{userlabel}"
               x="{x}"
               y="{y}">
          <configuration>
            <noaction/>
          </configuration>
          <dragpoints>
{dragpoints}
          </dragpoints>
        </shape>"""

# Stop/Return Documents Shape Template
RETURN_DOCUMENTS_SHAPE_TEMPLATE = """        <shape image="returndocuments_icon"
               name="{name}"
               shapetype="returndocuments"
               userlabel="{userlabel}"
               x="{x}"
               y="{y}">
          <configuration>
            <returndocuments label="{label}"/>
          </configuration>
          <dragpoints/>
        </shape>"""

# Map Shape Template
MAP_SHAPE_TEMPLATE = """        <shape image="map_icon"
               name="{name}"
               shapetype="map"
               userlabel="{userlabel}"
               x="{x}"
               y="{y}">
          <configuration>
            <map mapId="{map_id}"/>
          </configuration>
          <dragpoints>
{dragpoints}
          </dragpoints>
        </shape>"""

# Document Properties Shape Template
DOCUMENT_PROPERTIES_SHAPE_TEMPLATE = """        <shape image="documentproperties_icon"
               name="{name}"
               shapetype="documentproperties"
               userlabel="{userlabel}"
               x="{x}"
               y="{y}">
          <configuration>
            <documentproperties>
{properties}
            </documentproperties>
          </configuration>
          <dragpoints>
{dragpoints}
          </dragpoints>
        </shape>"""

# Branch Shape Template
BRANCH_SHAPE_TEMPLATE = """        <shape image="branch_icon"
               name="{name}"
               shapetype="branch"
               userlabel="{userlabel}"
               x="{x}"
               y="{y}">
          <configuration>
            <branch numBranches="{num_branches}"/>
          </configuration>
          <dragpoints>
{dragpoints}
          </dragpoints>
        </shape>"""

# Note Shape Template (for documentation)
NOTE_SHAPE_TEMPLATE = """        <shape image="note_icon"
               name="{name}"
               shapetype="note"
               x="{x}"
               y="{y}">
          <configuration>
            <note createdBy="{created_by}">
              <noteText>{note_text}</noteText>
            </note>
          </configuration>
          <dragpoints/>
        </shape>"""

# Dragpoint Template (reusable)
DRAGPOINT_TEMPLATE = """            <dragpoint name="{name}"
                       toShape="{to_shape}"
                       x="{x}"
                       y="{y}"/>"""

# Dragpoint with identifier (for branches)
DRAGPOINT_BRANCH_TEMPLATE = """            <dragpoint identifier="{identifier}"
                       name="{name}"
                       text="{text}"
                       toShape="{to_shape}"
                       x="{x}"
                       y="{y}"/>"""

__all__ = [
    "START_SHAPE_TEMPLATE",
    "RETURN_DOCUMENTS_SHAPE_TEMPLATE",
    "MAP_SHAPE_TEMPLATE",
    "DOCUMENT_PROPERTIES_SHAPE_TEMPLATE",
    "BRANCH_SHAPE_TEMPLATE",
    "NOTE_SHAPE_TEMPLATE",
    "DRAGPOINT_TEMPLATE",
    "DRAGPOINT_BRANCH_TEMPLATE",
]
