def create_file(dic):
    #template
    template = DocxTemplate("template.docx")
    #dates
    today = date.today()
    todayformated = today.strftime("%Y%m%d")

    #dictionary for merging = {"VariableWord" : "Input"}
    DicForMerging = dic
    template.render(DicForMerging)
    filepath = f"./{date}_file.docx"
    template.save(filepath)
    return filepath