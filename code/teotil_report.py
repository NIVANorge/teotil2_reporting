import os

import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.xmlchemy import OxmlElement
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

plt.style.use("ggplot")


def insert_para_after(para, style="Normal", align="center"):
    """Insert a new paragraph after the given paragraph.

    Args:
        para:     Obj. Paragraph object to insert after
        style:    Str. One of Word's pre-defined styles
        align:    Str. One of 'left', 'center' or 'right'

    Returns:
        Paragraph object.
    """
    new_p = OxmlElement("w:p")
    para._p.addnext(new_p)
    new_para = Paragraph(new_p, para._parent)

    new_para.style = style

    if align == "center":
        new_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        new_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif align == "right":
        new_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        raise ValueError("'align' must be one of 'left', 'center' or 'right'.")

    return new_para


def insert_image(para, img_path, width_cm=15):
    """Insert an image into a paragraph.

    Args:
        para:     Obj. Paragraph object to insert after
        img_path: Str. Path to image
        width_cm: Float. Width of image in cm

    Returns:
        Run object.
    """
    run = para.add_run()
    run.add_picture(img_path, width=Cm(width_cm))

    return run


def insert_table(doc, para, df, table_style="Grid Table 4 Accent 1"):
    """Insert a dataframe as a table into the given paragraph.

    Args:
        doc:         Obj. Document object
        para:        Obj. Paragraph object to insert after
        df:          Obj. Dataframe with table data
        table_style: Str. Word table style to apply. NOTE: If your template document
                     doesn't contain any styled tables, the list of available choices
                     may be very limited. Try

                         styles = doc.styles
                         table_styles = [s for s in styles if s.type == WD_STYLE_TYPE.TABLE]

                     to see a list of available styles in your document. To add a style,
                     manually create a table with the desired style in the template, then save
                     it, delete the table and save again. The chosen style should now be
                     available

    Returns:
        None.
    """
    df = df.copy().astype(str)
    df.replace("<NA>", "", inplace=True)

    # Tables can only be added at the end of the document, but they can be moved
    # elsewhere afterwards. See
    # https://github.com/python-openxml/python-docx/issues/156
    table = doc.add_table(df.shape[0] + 1, df.shape[1])
    table.style = table_style

    # Add header
    for j in range(df.shape[-1]):
        table.cell(0, j).text = df.columns[j]
        table.cell(0, j).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Add data
    for i in range(df.shape[0]):
        for j in range(df.shape[-1]):
            table.cell(i + 1, j).text = str(df.values[i, j])
            table.cell(i + 1, j).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Move to desired location (paragraph)
    tbl, p = table._tbl, para._p
    p.addnext(tbl)


def make_plot(df, title, base_path, year):
    """Create a time series plot from a dataframe.

    Args:
        df:        Obj. Dataframe with table data
        title:     Str. Title for plot
        base_path: Str. File path for original CSV data table

    Returns:
        Plot path. Plot is saved to ./plots/
    """
    df = df.copy()

    if base_path[-5] == "p":
        ylabel = "Fosfor (tonn)"
    elif base_path[-5] == "n":
        ylabel = "Nitrogen (tonn)"
    else:
        raise ValueError("Could not identify ylabel.")

    ax = df.set_index("År").plot(figsize=(8, 6), title=title, xlabel="", fontsize=12)
    ax.legend(
        loc="center", bbox_to_anchor=(0.5, -0.2), ncol=3, prop={"size": 12}
    ).get_frame().set_boxstyle("Round", pad=0.2, rounding_size=0.5)
    ax.set_ylabel(ylabel, fontdict={"fontsize": 12, "fontweight": "bold"})
    plt.tight_layout()

    fname = os.path.split(base_path)[1][:-4]
    png_path = f"../report_{year}/plots/{fname}_plot.png"
    plt.savefig(png_path, dpi=200)
    plt.close()

    return png_path


def read_data_table(fpath, heading):
    """Reads a CSV to a dataframe. Rounds values to integers and adds
    an extra row for 1985 at the start of each time series.

    Args:
        fpath: Path to CSV data

    Returns:
        Dataframe
    """
    # Read 1985 data
    csv_path = r"../jse_data_1985/data_1985.csv"
    df_85 = pd.read_csv(csv_path, index_col="section_name")

    # Read model data
    df = pd.read_csv(fpath)

    # Correct typo in Jose's column names
    df.rename({"Bakgrun": "Bakgrunn"}, axis="columns", inplace=True)

    # Insert data from 1985 if relevant
    if heading in df_85.index:
        row_85 = df_85.loc[[heading]]
        df = pd.concat([row_85, df], axis="rows")

    df.reset_index(inplace=True, drop=True)
    df.sort_values("År", inplace=True)
    header = [
        "År",
        "Akvakultur",
        "Jordbruk",
        "Befolkning",
        "Industri",
        "Bakgrunn",
        "Totalt",
        "Menneskeskapt",
    ]
    df = df[header]
    df = df.round(0).astype("Int64")

    # Rename col as requested by Rita Vigdis
    df.rename({"Befolkning": "Avløp"}, axis="columns", inplace=True)

    return df
