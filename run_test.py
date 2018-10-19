#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import commands
import threading
import time
import subprocess
from util import logger
from util import get_sn
from util import writeResult
from util import command
from util import writeExcel
from util import creatExcel
from os import popen

reload(sys)  # 重新加载sys
sys.setdefaultencoding('utf8')
logname = "log-host.txt"


class Worker():
    def getAPKsList(self, apk_folder):
        apk_path = apk_folder
        apks = commands.getoutput('ls %s | grep apk' % apk_path)
        apk_list = apks.split('\n')
        if len(apk_list) != 0:
            return apk_list
        else:
            logger(logname, 'No APK file in %s' % apk_path)
            # r.set('apk_list',apk_list)
            return []

    def installAPK(self, sn, apk):

        try:
            apk_path = os.path.join(APK_FOLDER, apk)
            installCmd = r'adb -s %s install -r %s' % (sn, apk_path)
            logger(logname, sn + ": installAPK begin : " + installCmd)
            subp = subprocess.Popen(installCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while subp.poll() is None:
                subp.stdout.readline()
            logger(logname, sn + ": install returncode = " + str(subp.returncode))
            if subp.returncode == 0:  # return code 为0表示成功
                return True
            else:
                return False
        except Exception, e:
            logger(logname, sn + e.message)
            os.system("adb -s %s shell input keyevent 3" % sn)
            return False
        finally:
            os.system("adb -s %s shell input keyevent 3" % sn)

    def launchAPK(self, sn, apk):
        apk_cmp = apk
        logger(logname, sn + ": lunching %s" % apk_cmp)
        results = command("adb -s %s shell ' am start -W %s'" % (sn, apk_cmp), timeout=30).strip().replace('\n', ';')
        if 'Complete' in results:
            return True
        else:
            return False

    def uninstallAPK(self, sn, apk):
        apk_packageName = apk
        result = commands.getoutput('adb -s %s uninstall %s' % (sn, apk_packageName))
        logger(logname, sn + ": uninstallAPK apk_packageName = " + apk_packageName + ";result=  " + result)
        if 'Success' in result.strip().replace("\r", ""):
            check_result = commands.getoutput('adb -s %s shell pm list packages -f | grep %s' % (sn, apk_packageName))
            logger(logname,
                   sn + ": uninstallAPK apk_packageName = " + apk_packageName + ";check_result=  " + check_result)
            if check_result == '':
                return True
            return False
        else:
            return False


class runingThread(threading.Thread):

    def __init__(self, sn, apk_list):
        threading.Thread.__init__(self)
        self.sn = sn
        self.apk_list = apk_list

    def run(self):
        global index
        testnum = 0
        while index < len(self.apk_list) - 1:
            lock.acquire()
            index = index + 1
            testnum = index
            lock.release()
            logger(logname, self.sn + ": run test begin apk =" + self.apk_list[testnum] + ";testnum =" + str(testnum))
            run_test(self.sn, self.apk_list[testnum], testnum)


index = -1


def get_start_activity(apk_path):
    result = popen("aapt dump xmltree %s AndroidManifest.xml" % apk_path)
    resu = result.read().strip().split('\n')
    content = []
    start_activity = ""
    package_name = ""
    new_content = []
    # print resu
    for res in resu:
        if '="android.intent.category.LAUNCHER"' in res:
            line = resu.index(res)
            while not "E: activity " in resu[line]:
                content.append(resu[line])
                line = line - 1
        if "package=" in res:
            package_name = res.strip().split('=')[1].split()[0].strip('"')
    content.reverse()
    for con in content:
        # print "before ="+con
        if not "E: intent-filter" in con:
            new_content.append(con)
        else:
            break
    for con in new_content:
        # print "after ="+con
        if "android:name" in con:
            start_activity = package_name + '/' + con.split('=')[1].split(' ')[0].strip('"')
            break
    if start_activity == "":
        for con in new_content:
            if "Activity" in con:
                start_activity = package_name + '/' + con.split('"')[1]
    return package_name, start_activity


def run_test(sn, apk, testnum):
    logger(logname, sn + ": apk :" + apk + ", index :" + str(testnum))
    install_result = 'fail'
    uninstall_result = 'fail'
    launch_result = 'fail'
    apk_path = os.path.join(APK_FOLDER, apk)
    package_name, class_name = get_start_activity(apk_path)
    logger(logname,
           sn + ": run_test apk_path :" + apk_path + ", package_name :" + package_name + ";class_name = " + class_name)
    if Worker().installAPK(sn, apk):
        install_result = 'pass'
        time.sleep(2)

        if Worker().launchAPK(sn, class_name):
            launch_result = 'pass'
        else:
            launch_result = 'fail'
        time.sleep(90)
        os.system("adb -s %s shell input keyevent 3" % sn)
        time.sleep(2)
        if Worker().uninstallAPK(sn, package_name):
            uninstall_result = 'pass'
            time.sleep(2)
        else:
            uninstall_result = 'fail'
    else:
        install_result = 'fail'
        launch_result = 'fail'
        uninstall_result = 'fail'
    logger(logname, sn + ': result apk:' + apk)
    logger(logname,
           sn + ': result install:' + install_result + '; launch:' + launch_result + '; uninstall:' + uninstall_result)
    # 添加输出excel表格
    filepath = os.getcwd() + os.sep + "result_%s.txt" % (sn)
    writeResult(package_name, install_result, launch_result, uninstall_result, filepath)
    logger(logname, sn + ': ' + '>' * 20 + ' DONE %s ' % testnum + '<' * 20 + "\n" * 2)


def delete_old_logs():
    files = os.listdir(os.getcwd())
    for file in files:
        if os.path.isfile(file):
            if "log" in file or "result" in file:
                os.remove(os.getcwd() + os.sep + file)


def getresult(sn, sor, des):
    if os.path.isfile(sor):
        co = open(sor, 'r')
        con = co.readline().strip()
        while not con == '':
            item = con.split("\t,")
            re = [sn]
            re.extend(item)
            writeExcel(re, des)
            con = co.readline().strip()


if __name__ == '__main__':
    delete_old_logs()
    sns = get_sn()
    APK_FOLDER = os.path.join(os.getcwd(), "apk")
    apk_list = Worker().getAPKsList(APK_FOLDER)
    lock = threading.Lock()
    for apk in apk_list:
        apk_path = os.path.join(APK_FOLDER, apk)
        packageName, start = get_start_activity(apk_path)
        print packageName
        print start
    result_excel = os.getcwd() + os.sep + "result.xls"
    host_log = os.getcwd() + os.sep + "log-host.txt"
    creatExcel(["SN", "PackageName", "Install_result", "Lunch_result", "Uninstall_result"], result_excel)
    start_time = time.time()
    logger(logname, "start time :" + str(start_time))
    logger(logname, 'main apk total num:' + str(len(apk_list)) + "; SNS = " + str(sns))
    for sn in sns:
        i = sns.index(sn)
        ti = runingThread(sn, apk_list)
        ti.start()
    for sn in sns:
        i = sns.index(sn)
        ti.join()
    hostLog = open(host_log, 'r')
    logcon = hostLog.read().strip().split('\n')
    hostLog.close()
    end_time = time.time()
    logger(logname, "end time :" + str(end_time))
    for context in logcon:
        for sn in sns:
            logname_sn = os.getcwd() + os.sep + "log_%s.log" % (sn)
            con = open(logname_sn, 'a')
            if sn + ':' in context:
                con.write(context.split(": ")[1] + '\n')
            if sn + '>' in context:
                con.write(context.split(": ")[1] + '\n' * 3)
            con.close()
    for sn in sns:
        sor = os.path.join(os.getcwd(), "result_%s.txt" % sn)
        des = result_excel
        getresult(sn, sor, des)
    spend_time = end_time - start_time
    logger(logname, '>' * 20 + "Test Finished" + '<' * 20)
    logger(logname, "spend_time =" + str(spend_time))
    writeExcel([start_time, end_time, spend_time], result_excel)
    sys.exit(0)
