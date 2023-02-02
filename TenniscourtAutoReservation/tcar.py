from multiprocessing import Process, Queue
from subprocess import TimeoutExpired
import time
import os
import platform

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import ui
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if platform.system() == 'Windows':
    chrome_webdriver = os.path.dirname(os.path.realpath(__file__)) + "\chromedriver.exe"
else:
    chrome_webdriver = os.path.dirname(os.path.realpath(__file__)) + "/chromedriver"

rent_time_str = ("06:00~08:00", "08:00~10:00", "10:00~12:00", "12:00~14:00", "14:00~16:00", "16:00~18:00", "18:00~20:00", "20:00~22:00")

##########################################################################
#
# 시간까지 대기
#
##########################################################################
def wait_time(time_hour, time_min):
    while(1):
        now = time.localtime()
        if(now.tm_hour == time_hour and now.tm_min >= time_min):
            print("Time!!!!!!!!")
            break

##########################################################################
#
# page 에 Footer 가 로드될떄까지 대기
#
##########################################################################
def page_is_loaded(br):
    return br.find_element_by_id("Footer") != None

##########################################################################
#
# id와 pw 로 login
#
##########################################################################
def login(userid, passwd, x = 0, y = 0):

    # USB error ignore option
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
    br = webdriver.Chrome(options=options, executable_path=chrome_webdriver)
    
    br.set_window_position(x, y)
    br.set_window_size(500,800)
    br.get("https://yeyak.gys.or.kr/fmcs/27?referer=https%3A%2F%2Fdaehwa.gys.or.kr%2Fmember%2Flogin.php%3FpreURL%3D%252Frent%252Ftennis_rent.php&login_check=skip")

    elem = br.find_element_by_id("userId")
    elem.clear()
    elem.send_keys(userid)
    elem = br.find_element_by_id("userPassword")
    elem.send_keys(passwd)
    elem.send_keys(Keys.RETURN)
     
    br.get("https://daehwa.gys.or.kr:451/rent/tennis_rent.php")

    wait = ui.WebDriverWait(br, 10)
    wait.until(page_is_loaded)

    return br

##########################################################################
#
# 예약 날자 선택
#
##########################################################################
def SelectRentDay(br, RentDay):

    # select next month
    nextmonth = br.find_element_by_xpath('//*[@id="content"]/div[3]/div/form/div[3]/div/div/div[2]/a[2]')
    nextmonth.send_keys(Keys.ENTER)

    # select rent day(2021-06-22)
    selectitem = br.find_element_by_xpath('//*[@id="' + RentDay + '"]/a')
    selectitem.send_keys(Keys.ENTER)

##########################################################################
#
# 예약 코트
#
##########################################################################
def SelectRentCourtNo(br, CourtNo):
    
    # select court(No.1 court - 1, ...)
    selectitem = Select(br.find_element_by_xpath('//*[@id="content"]/div[3]/div/form/div[4]/ul/li[2]/select'))
    selectitem.select_by_index(CourtNo)

##########################################################################
#
# 예약 시간 1: 06:00~08:00, 2:08:00~10:00, ...
#
##########################################################################
def SelectRentTime(br, RentTime):

    # select time(6:00~8:00, ...)
    renttime_str = "//input[@name='rent_chk[]']"
    renttimes = br.find_elements_by_xpath(renttime_str)

    renttimeindex = 1
    for rent in renttimes:

        #print(rent.get_attribute('value')) 
        if renttimeindex == RentTime:
            br.execute_script("arguments[0].click();", rent)
            print("Select Time : %s"%(rent.get_attribute('value')))
            return
        renttimeindex = renttimeindex + 1
    
##########################################################################
#
# 대관신청
#
##########################################################################
def RentApply(br):
    # Rent!
    selectitem = br.find_element_by_xpath('//*[@id="content"]/div[3]/div/form/div[10]/span/a')
    selectitem.send_keys(Keys.ENTER)


##########################################################################
#
# 개인정보 및 대관신청서 작성
#
##########################################################################
def RentalApplicationSubmission(br):
    
    try:
        WebDriverWait(chrome_webdriver, 5, EC.element_attribute_to_include(By.XPATH, '//*[@id="rent_doc"]/form/table/tbody/tr[11]/td/div/input'))
    except:
        print("Timeout RentalApplicationSubmission")
        return
    
    # check agree1
    selectitem = br.find_element_by_xpath('//*[@id="rent_doc"]/form/table/tbody/tr[11]/td/div/label/input')
    selectitem.click()

    # check agree2
    selectitem = br.find_element_by_xpath('//*[@id="rent_doc"]/form/table/tbody/tr[13]/td/div/label/input')
    selectitem.click()

    # Application submission
    selectitem = br.find_element_by_xpath('//*[@id="rent_doc"]/form/table/tbody/tr[14]/td/center/a[1]')
    selectitem.send_keys(Keys.ENTER)

    #final OK!
    WebDriverWait(br, 10).until(EC.alert_is_present())
    # 아래 주석을 제거해야 최정적으로 예약함
    br.switch_to.alert.accept()

##########################################################################
#
# 현재 웹 Page 가 예약 가능한 상태 확인
#
##########################################################################
def PageReady(br):

    image_elements = br.find_elements_by_xpath("//img[@src='/images/rent/sub_rent_btn_rent.gif']")

    for image in image_elements:
        img_src = image.get_attribute("src")
        if(img_src == 'https://daehwa.gys.or.kr:451/images/rent/sub_rent_btn_rent.gif'):
            return True
        
    return False
    
##########################################################################
#
# 예약 메인
# CourtNo 1,2,3,4
# ReentTime 06:00 - 1, 08:00 2, ...
#
##########################################################################
def auto_rent(userid, passwd, RentDay, CourtNo, RentTime, x , y):

    print("Macro log in : %s"%(userid))
    br = login(userid, passwd, x, y)

    print("Select Court")
    SelectRentCourtNo(br, CourtNo)
    print("Select Day")
    SelectRentDay(br, RentDay)

    print("Wait Time....")
    # wait 10:00 AM and Page Ready?
    wait_time(10, 0)

    count = 0
    while(1):
        if(PageReady(br) == True):
            print("Page Ready")
            break

        print("Page Refresh")
        br.refresh()
        time.sleep(1)

        count = count + 1
        if(count > 60): # 1 min
            print("Page Timeover")
            break

    if(count > 10):
        print("Reseravation fail : Page not ready")
        return

    SelectRentTime(br, RentTime)

    start_time = time.localtime()
    print("Macro Rent Start : %s, CourtNo : %d, Time : %s, Start : %d:%d:%d"
    %(RentDay, CourtNo, rent_time_str[RentTime],start_time.tm_hour, start_time.tm_min,start_time.tm_sec))

    RentApply(br)

    try:
        alert = br.switch_to.alert
        print(alert.text)
        print("Reseravation fail : Select time is already reservation")
        return
    except:
        print("Write Rent Application..")

    try:
        # New Window : Rental Application
        WebDriverWait(br, timeout=5).until(EC.number_of_windows_to_be(2))
        br.switch_to.window(br.window_handles[-1])
    except TimeoutException as ex:
        print("WebDriverWait TimeoutException encountered")
        return
    
    time.sleep(1)
    br.set_window_position(x, y)

    RentalApplicationSubmission(br)

    end_time = time.localtime()
    total_sec = (end_time.tm_min*60+end_time.tm_sec) - (start_time.tm_min*60+start_time.tm_sec)
    print("Macro Rent End : %s, CourtNo : %d, Time : %s, End : %d:%d:%d, Laptime : %d"
    %(RentDay, CourtNo, rent_time_str[RentTime], end_time.tm_hour, end_time.tm_min,end_time.tm_sec, total_sec))



##########################################################################
#
#
#
##########################################################################
def main():

    #while(1):
    #    now = time.localtime()
    #    print("%d:%d"%(now.tm_hour,now.tm_min))
    #    time.sleep(30)

    # userid, passwd, 날짜, 코트(1-4), 시간(06:00~ 1번 08:00~ 2번), 화면x, 화면y
    p1 = Process(target=auto_rent, args=("hongyver", "hongyver12", "2022-06-02", 4, 2 , 0, 0))
    p2 = Process(target=auto_rent, args=("hongyver", "hongyver12", "2022-06-03", 4, 2, 100, 0))

    # p3 = Process(target=auto_rent, args=("hongyver", "hongyver12", "2022-06-19", 4, 2, 1000, 0))
    # p4 = Process(target=auto_rent, args=("hongyver", "hongyver12", "2022-06-26", 4, 2, 0, 300))

    # p5 = Process(target=auto_rent, args=("hongyver", "hongyver12", "2022-06-18", 2, 1, 500, 300))
    # p6 = Process(target=auto_rent, args=("hongyver", "hongyver12", "2022-06-25", 2, 1, 1000, 300))

    # p7 = Process(target=auto_rent, args=("jmk479", "!kj542654", "2022-06-06", 4, 3, 0, 600))
    # p8 = Process(target=auto_rent, args=("jmk479", "!kj542654", "2022-06-12", 4, 1, 500, 600))

    # p9 = Process(target=auto_rent, args=("jmk479", "!kj542654", "2022-06-19", 4, 1, 1000, 600))
    # p10 = Process(target=auto_rent, args=("jmk479", "!kj542654", "2022-06-26", 4, 1, 0, 800))

    # p11 = Process(target=auto_rent, args=("hongyver", "hongyver12", "2022-06-06", 4, 2 , 250, 0))
    # p12 = Process(target=auto_rent, args=("jmk479", "!kj542654", "2022-06-05", 4, 1, 0, 800))

    #p9 = Process(target=auto_rent, args=("jmk479", "hongyver12", "2022-02-28", 3, 2, 1000, 600))
    #p10 = Process(target=auto_rent, args=("william42", "tazz8212!!!", "2022-02-28", 2, 3, 0, 800))

    p1.start()
    p2.start()

    # p3.start()
    # p4.start()

    # p5.start()
    # p6.start()

    # p7.start()
    # p8.start()
    
    # p9.start()
    # p10.start()

    # p11.start()
    # p12.start()

    p1.join()
    p2.join()

    # p3.join()
    # p4.join()

    # p5.join()
    # p6.join()

    # p7.join()
    # p8.join()

    # p9.join()
    # p10.join()

    # p11.join()
    # p12.join()

if __name__ == "__main__":
	main()
