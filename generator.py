import reportlab.pdfgen.canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black

(width, height) = A4


def create_canvas(name):
    return reportlab.pdfgen.canvas.Canvas(name, pagesize=A4)


def generate(model, uid, canvas):
    for page in model.pages:
        draw_page(page, uid, model.name, canvas)


def draw_qr_data(canvas, data, size, position):
    qr = QrCodeWidget(data)
    qr_draw = Drawing(size, size, transform=[size/qr.barWidth,0,0,size/qr.barHeight,0,0])
    qr_draw.add(qr)
    renderPDF.draw(qr_draw, canvas, position[0], position[1])


def draw_page(page, uid, survey_name, canvas : reportlab.pdfgen.canvas.Canvas):
    draw_qr_data(canvas, 'survey:'+survey_name+':'+page.name+':'+uid, 64, (48, height-64-48))
    canvas.setFillColorRGB(0.2, 0.2, 0.2)
    canvas.setStrokeColorRGB(0.2, 0.2, 0.2)
    canvas.circle(32, 32, 4, stroke=1, fill=1)
    canvas.circle(32+12, 32, 4, stroke=1, fill=1)
    canvas.circle(32, 32+12, 4, stroke=1, fill=1)
    canvas.circle(width - 32, height - 32, 4, stroke=1, fill=1)
    canvas.circle(width - 32-12, height - 32, 4, stroke=1, fill=1)
    canvas.circle(width - 32, height - 32-12, 4, stroke=1, fill=1)
    canvas.circle(width - 32, 32, 4, stroke=1, fill=1)
    canvas.circle(width - 32-12, 32, 4, stroke=1, fill=1)
    canvas.circle(width - 32, 32+12, 4, stroke=1, fill=1)
    canvas.circle(32, height - 32, 4, stroke=1, fill=1)
    canvas.circle(32+12, height - 32, 4, stroke=1, fill=1)
    canvas.circle(32, height - 32-12, 4, stroke=1, fill=1)

    canvas.setFillColorRGB(0.3, 0.3, 0.3)
    canvas.drawString(128, height - 67, survey_name+':'+page.name+':'+uid)

    canvas.setFillColorRGB(0.4, 0.4, 0.4)
    canvas.setStrokeColorRGB(0.2, 0.2, 0.2)
    canvas.setFont('Courier', 8)
    for field in page.get_binary_fields():
        canvas.circle(field.position[0], height - field.position[1], 5, stroke=1, fill=0)
        canvas.drawCentredString(field.position[0], height - field.position[1]-2, field.hint)

    canvas.setFillColorRGB(0.1, 0.1, 0.1)
    for text in page.get_text_areas():
        if text.rotation != 0:
            canvas.saveState()
            canvas.rotate(text.rotation)
        tobj = canvas.beginText(text.position[0], height - text.position[1])
        tobj.setFont(text.fontname, text.fontsize)
        for line in text.text.split():
            tobj.textLine(line)
        canvas.drawText(tobj)

        if text.rotation != 0:
            canvas.restoreState()
    canvas.showPage()
