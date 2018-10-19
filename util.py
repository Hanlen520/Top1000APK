#! /usr/bin/env python
# -*-coding:utf-8-*-

import os
import logging
import time
import subprocess
from copy import copy
from xlrd import open_workbook
from xlutils.copy import copy
from xlwt import Workbook

import xlrd as xlrd


def command(cmd, timeout=10):
    """
        excute adb shell command
    :param cmd:
    :param timeout:
    :return:
    """
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    t_beginning = time.time()
    seconds_passed = 0
    while True:
        if p.poll() is not None:
            break
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            p.terminate()
            p.wait()
            return "Fail"
            # raise Exception('Time Out!!!')
    return p.stdout.read()


def logger(logname, strs):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a-%d-%b-%Y %H:%M:%S',
                        filename=logname,
                        filemode='w')
    logging.info(strs)
    print strs


def writeResult(apk_name, install_result, launch_result, uninstall_result, result_file):
    file_object = open(result_file, 'a')
    file_object.writelines(
        '%s,%s,%s,%s\n' % (apk_name + '\t', install_result + '\t', launch_result + '\t', uninstall_result))
    file_object.close()


def creatExcel(args, excel_path):
    print "创建excel文件"
    book = Workbook(encoding='utf-8')

    sheet_result = book.add_sheet('测试结果')

    for num in range(len(args)):
        sheet_result.write(0, num, args[num])
    # 保存Excel book.save('path/文件名称.xls')
    book.save(excel_path)


def writeExcel(args, excel_path):
    try:
        rexcel = open_workbook(excel_path)  # 用wlrd提供的方法读取一个excel文件
        rows = rexcel.sheets()[0].nrows  # 用wlrd提供的方法获得现在已有的行数
        excel = copy(rexcel)  # 用xlutils提供的copy方法将xlrd的对象转化为xlwt的对象
        table = excel.get_sheet(0)  # 用xlwt对象的方法获得要操作的sheet
        row = rows
        for dex in range(len(args)):
            table.write(row, dex, args[dex])  # xlwt对象的写方法，参数分别是行、列、值
        excel.save(excel_path)  # xlwt对象的保存方法，这时便覆盖掉了原来的excel
    except Exception ,e:

        print e.message



def get_sn():
    sn = []
    mess = os.popen('adb devices').readlines()
    for i in mess[1::]:
        i.strip()
        if 'device' in i:
            sn.append(i.split('\t')[0])
    return sn
