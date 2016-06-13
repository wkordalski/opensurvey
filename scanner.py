import sane
import libzbar as zbar
import numpy as np
import cv2 as cv
from reportlab.lib.pagesizes import A4

from model import Model


def hypot(a, b):
    return (int(a[0]) - int(b[0])) ** 2 + (int(a[1]) - int(b[1])) ** 2


def get_containers_by_qr_symbol(symbols, model: Model, results):
    survey_symbol = None
    page = None
    set_id = None

    for symbol in symbols:
        data = symbol.data.decode('utf-8')
        survey_data = data.split(':')
        if data.startswith('survey:') and len(survey_data) == 4:
            survey_id = survey_data[1]
            if survey_id != model.name:
                continue
            page = model.get_page_by_name(survey_data[2])
            if not page:
                continue
            set_id = survey_data[3]
            if set_id not in results:
                results[set_id] = dict()
            survey_symbol = symbol
    if not survey_symbol:
        return None

    return survey_symbol, page, results[set_id]


def align_page(im, survey_symbol, scale):
    gs = np.array(im)
    bgs = cv.medianBlur(gs, 5)
    cv.imwrite('blured.png', bgs)
    circles = cv.HoughCircles(bgs, cv.HOUGH_GRADIENT, 1, 20, param1=50,param2=30,minRadius=10, maxRadius=15)
    circles = np.uint16(np.around(circles))

    cimg = cv.cvtColor(gs,cv.COLOR_GRAY2BGR)

    for i in circles[0,:]:
        # draw the outer circle
        cv.circle(cimg,(i[0],i[1]),i[2]-5,(0,255,0),2)
        # draw the center of the circle
        cv.circle(cimg,(i[0],i[1]),2,(0,0,255),3)


    cv.imwrite('align.png', cimg)

    ngh_cir = set()
    for i, ic in enumerate(circles[0, :]):
        for j, jc in enumerate(circles[0, :]):
            if 400 < hypot(ic, jc) < 1600:
                if i < j:
                    ngh_cir.add((i, j))
    corners = set()
    for a, b in ngh_cir:
        for c, d in ngh_cir:
            if a == c and b == d:
                continue
            if b == c and 1600 < hypot(circles[0, a], circles[0, d]) < 3200:
                corners.add(b)
            if a == c and 1600 < hypot(circles[0, b], circles[0, d]) < 3200:
                corners.add(a)
            if b == d and 1600 < hypot(circles[0, a], circles[0, c]) < 3200:
                corners.add(b)
            if a == d and 1600 < hypot(circles[0, b], circles[0, c]) < 3200:
                corners.add(a)

    if len(corners) < 4:
        print("Could not find align patterns")
        return None

    tl = None
    for i in corners:
        if 7000 < hypot(survey_symbol.locator[0], circles[0, i]) < 10000:
            tl = i
            break
    if not tl:
        print("Could not find top-left identification pattern.")
        return None
    corners.remove(tl)

    loc = survey_symbol.locator
    veh = (np.int32(loc[3]) - np.int32(loc[0]))
    vev = (np.int32(loc[1]) - np.int32(loc[0]))

    def find_most_distant(i):
        originated = np.int32(circles[0,i][0:2]) - np.int32(loc[2])
        return int(np.sum(originated * veh)) + int(np.sum(originated * vev))
    br = max(corners, key=find_most_distant)
    corners.remove(br)

    def find_top_right(i):
        originated = np.int32(circles[0,i][0:2]) - np.int32(loc[3])
        if np.sum(originated * vev) >= 0:
            return 0
        else:
            return int(np.sum(originated * veh))
    tr = max(corners, key=find_top_right)
    corners.remove(tr)

    def find_bottom_left(i):
        originated = np.int32(circles[0,i][0:2]) - np.int32(loc[1])
        if np.sum(originated * veh) >= 0:
            return 0
        else:
            return int(np.sum(originated * vev))
    bl = max(corners, key=find_bottom_left)
    corners.remove(bl)

    w, h = A4
    w *= scale
    h *= scale
    m = 32 * scale
    print(A4)
    ptr = cv.getPerspectiveTransform(np.float32([circles[0,tl][0:2], circles[0,tr][0:2], circles[0,br][0:2], circles[0,bl][0:2]]),
                                     np.float32([(m, m), (w-m, m), (w-m, h-m), (m, h-m)]))

    btim = cv.warpPerspective(bgs, ptr, (int(w), int(h)))
    tim = cv.warpPerspective(gs, ptr, (int(w), int(h)))
    return tim, btim


def scan_page(im, m, r):
    symbols = zbar.Image.from_im(im).scan()
    containers = get_containers_by_qr_symbol(symbols, m, r)
    if not containers:
        print("Could not find QR identification pattern")
        return False
    survey_symbol, page, results = containers
    scale = 2.8
    imgs = align_page(im, survey_symbol, scale)
    if imgs is None:
        return False

    img, bimg = imgs

    cimg = cv.cvtColor(img,cv.COLOR_GRAY2BGR)

    # find binary fields :D
    circles = cv.HoughCircles(bimg, cv.HOUGH_GRADIENT, 1, 20, param1=50,param2=30,minRadius=13, maxRadius=19)
    circles = np.uint16(np.around(circles))

    for i in circles[0,:]:
        # draw the outer circle
        cv.circle(cimg,(i[0],i[1]),i[2]-5,(0,255,0),2)
        # draw the center of the circle
        cv.circle(cimg,(i[0],i[1]),2,(0,0,255),3)

    for field in page.get_binary_fields():
        real_pos = (field.position[0]*scale, field.position[1]*scale)
        for circle in circles[0,:]:
            if hypot(real_pos, circle[0:2]) < 400:
                mask = np.zeros(bimg.shape, dtype=np.uint8)
                cv.circle(mask, (circle[0], circle[1]), circle[2]-5, (255,), -1)
                avg = cv.mean(bimg, mask)[0]
                print(avg)
                results[field.name] = (avg < 170)

    cv.imwrite('output.png', cimg)


def main(model, results):
    sane.init()
    print("Loading scanner devices...")
    devices = sane.get_devices()
    if len(devices) == 0:
        print("No devices available.")
        return
    print(" Id Vendor                         Product")
    print("-"*80)
    for idx, device in enumerate(devices):
        print(str(idx).rjust(3) + " " + device[1].ljust(30)[:30] + " " + device[2].ljust(46)[:46])
    while True:
        try:
            dev_id = int(input("Device ID: "))
            if not 0 <= dev_id < len(devices):
                print("Device id must be number between 0 and {}.".format(len(devices) - 1))
            else:
                break
        except ValueError:
            print("Device id must be number between 0 and {}.".format(len(devices) - 1))
    try:
        device = sane.open(devices[dev_id][0])

        device.depth = 8
        device.mode = 'gray'
        device.resolution = 200

        # scan a page and to things...
        while True:
            while True:
                do_scan = input("Scan next page? [Y/n]  ")
                do_scan = do_scan.upper()
                if do_scan == 'Y' or do_scan == 'N' or do_scan == '':
                    break
            if do_scan == 'N':
                break

            device.start()
            im = device.snap()
            im.save('scanned.png')
            scan_page(im, model, results)
    finally:
        device.close()
    return
