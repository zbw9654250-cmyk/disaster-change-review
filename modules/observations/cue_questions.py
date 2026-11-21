"""Convert one retrieved observation into non-leading inspection prompts."""
def questions(note):
    axes = (
        (("错位","偏移","对齐","遮挡","重叠","位置差","模糊","清晰度"),
         "同一处轮廓在两期能对准吗？图像清晰度或遮挡对判断有什么影响？"),
        (("边缘","边界","轮廓","分界","界线","屋脊"),
         "选区内哪条可辨的边界可以作为参照？"),
        (("斑","块","带","条","纹","连续","散"),
         "选区里最容易指出的块状、条状或连续纹理是什么？"),
        (("亮","暗","深","浅","色"),
         "同一位置与紧邻屋面的相对明暗能看清吗？"),
    )
    items = [question for terms,question in axes if any(t in note for t in terms)][:2]
    return ("请对当前目标图核对以下观察问题，只陈述画面支持的答案。\n"+"\n".join(items)) if items else ""
