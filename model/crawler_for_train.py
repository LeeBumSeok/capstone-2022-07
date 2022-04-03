from multiprocessing.spawn import freeze_support
import multiprocessing
from numpy import negative
import requests
from bs4 import BeautifulSoup
import time
import urllib.request
from urllib.parse import urlparse
from multiprocessing import Manager, Pool, freeze_support  # Pool import하기
import csv
from datetime import datetime, timedelta
import codecs
import re

url = "http://api.seibro.or.kr/openapi/service/StockSvc/getKDRSecnInfo"  # 공공데이터포털 api 주소(Without param)
api_service_key_stock = "RXhGWArdgsytKaKf0g%2FWxNuo27wXxg4iChLUs9ePc39VvneddFbQ9v9ZXCDWJkdFbhqCvbw9kdMGy%2F%2Bv3it50A%3D%3D"  # service api key
api_decode_key_stock = requests.utils.unquote(
    api_service_key_stock, encoding="utf-8"
)  # api decode code

# Naver client key
client_id= "4NnYXQRzNVwTEO2_rwpd"
client_secret = "mZP8JBDOBK"
now = datetime.now()

# 시간 측정 함수
def logging_time(original_fn):
    def wrapper_fn(*args, **kwargs):
        start_time = time.time()
        result = original_fn(*args, **kwargs)
        end_time = time.time()
        print(
            "WorkingTime[{}]: {} sec".format(
                original_fn.__name__, end_time - start_time
            )
        )
        return result

    return wrapper_fn


# 종목 이름 가져오는 코드
@logging_time
def getStockCode(market, url_param):
    """
    market: 상장구분 (11=유가증권, 12=코스닥, 13=K-OTC, 14=코넥스, 50=기타비상장)
    """
    url_base = f"http://api.seibro.or.kr/openapi/service/{url_param}"
    url_spec = "getShotnByMartN1"
    url = url_base + "/" + url_spec
    api_key_decode = requests.utils.unquote(api_decode_key_stock, encoding="utf-8")

    params = {
        "serviceKey": api_key_decode,
        "pageNo": 1,
        "numOfRows": 100000,
        "martTpcd": market,
    }

    response = requests.get(url, params=params)
    # print(response.text)
    xml = BeautifulSoup(response.text, "lxml")
    items = xml.find("items")
    item_list = []
    for item in items:
        item_list.append(item.find("korsecnnm").text.strip())

    return item_list

def text_clean(inputString, query):
    # inputString = inputString.replace("<b>","").replace("</b>","") # html 태그 제거  ## <b> <b/>
    inputString = re.sub(r'\<[^)]*\>', '', inputString, 0).strip() # <> 안의 내용 제거  ## html태그 + 종목명
    inputString = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', ' ', inputString) # 특수문자 제거
    inputString = inputString.replace("&quot;"," ").replace("amp;","").replace("&gt; "," ").replace("&lt;"," ")
    inputString = inputString.replace(query," ")

    inputString = ' '.join(inputString.split())
    
    return inputString


# 크롤링 함수
def search_crawl(tuple_list,query):
    # 삭제할 키워드들 
    del_list = ["오늘의", "뉴스", "급락주","마감","주요","급등주"]

    page = 1
    maxpage = 3
    # 11= 2페이지 21=3페이지 31=4페이지  ...81=9페이지 , 91=10페이지, 101=11페이지
    maxpage_t = (int(maxpage) - 1) * 10 + 1
    sort = 0 #0=관련도순 1=최신순 
    while page <= maxpage_t:
        url = (
            "https://search.naver.com/search.naver?where=news&query=\""
            + query
            + "\"&sort="
            + str(sort)
            + "&start="
            + str(page)
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        html = response.text

        # 뷰티풀소프의 인자값 지정
        soup = BeautifulSoup(html, "html.parser")
        atags = soup.select(".news_tit")
        news_name =""
        news_date =""
        news_url = ""
        pov_or_neg = 0 #긍부정 라벨링 값
        
        #긍부정 단어장 오픈
        with open("./negative_words.txt", encoding='utf-8') as neg:
            negative = neg.readlines()
        negative = [neg.replace("\n", "") for neg in negative]
    
        with open("./positive_words.txt", encoding='utf-8') as pos:
            positive = pos.readlines()
        positive = [pos.replace("\n", "") for pos in positive]


        # <a>태그에서 제목과 링크주소 추출
        # 기사 제목, 기사url 저장 
        for atag in atags:
            # title_text.append(atag.text)  # 제목
            # link_text.append(atag["href"])  # 링크주소
            news_name = atag.text
            if any(keyword in news_name for keyword in del_list):
                continue
            news_name = text_clean(news_name,query)
            news_url = atag["href"]
            label =0
            tag = ""

            for i in range(len(positive)):
                if news_name.find(positive[i]) != -1:
                    label = 1
                    tag = positive[i]
                    break
            for i in range(len(negative)):
                if news_name.find(negative[i]) != -1:
                    label = -1
                    tag = negative[i]
                    break
            
            if label == 1:
                pov_or_neg = 1
                #print("positive", j)
            elif label == -1 :
                pov_or_neg = -1
                #print("negative", j)
            elif label == 0:
                pov_or_neg = 0              

        # tuple_list.append((query, news_name, news_url, news_date, pov_or_neg))
            tuple_list.append((news_name, pov_or_neg, query, tag))

        page += 10


#cospi = getStockCode(11, "StockSvc")
# print(cospi)
#cosdak = getStockCode(12, "StockSvc")
cospi = [
    "동화약품",
    "케이알모터스",
    "경방",
    "메리츠화재해상보험",
    "삼양홀딩스",
    "삼양홀딩스1우",
    "하이트진로",
    "하이트진로2우",
    "유한양행",
    "유한양행1우",
    "씨제이대한통운",
    "하이트진로홀딩스",
    "하이트진로홀딩스1우",
    "두산",
    "두산1우",
    "두산2우",
    "성창기업지주",
    "디엘",
    "디엘1우",
    "유유제약",
    "유유제약1우",
    "유유제약2우",
    "일동홀딩스",
    "한국앤컴퍼니",
    "기아",
    "대유플러스",
    "노루홀딩스",
    "노루홀딩스1우",
    "한화손해보험",
    "삼화페인트공업",
    "롯데손해보험",
    "대원강업",
    "조선내화",
    "대동",
    "가온전선",
    "삼일제약",
    "흥국화재해상보험",
    "흥국화재해상보험1우",
    "흥국화재해상보험2우",
    "씨에스홀딩스",
    "동아쏘시오홀딩스",
    "천일고속",
    "에스케이하이닉스",
    "영풍",
    "LS네트웍스",
    "유수홀딩스",
    "현대건설",
    "현대건설1우",
    "이화산업",
    "삼성화재해상보험",
    "삼성화재해상보험1우",
    "화천기공",
    "강남제비스코",
    "한화",
    "한화1우",
    "보해양조",
    "유니온",
    "전방",
    "한국주철관공업",
    "DB 하이텍",
    "DB 하이텍1우",
    "페이퍼코리아",
    "씨제이",
    "씨제이1우",
    "제이더블유중외제약",
    "제이더블유중외제약1우",
    "제이더블유중외제약2우",
    "대한방직",
    "만호제강",
    "LX인터내셔널",
    "대한제분",
    "국보",
    "유진투자증권",
    "금호전기",
    "동국제강",
    "지에스글로벌",
    "남광토건",
    "부국증권",
    "부국증권1우",
    "상상인증권",
    "백광산업",
    "삼성제약",
    "에스지글로벌",
    "케이지케미칼",
    "태원물산",
    "세아베스틸",
    "대한전선",
    "현대해상화재보험",
    "BYC",
    "BYC1우",
    "삼부토건",
    "현대차증권",
    "SK증권",
    "SK증권1우",
    "동양",
    "동양1우",
    "동양2우",
    "동양3우",
    "디아이동일",
    "조비",
    "제일연마공업",
    "금양",
    "케이비아이동국실업",
    "종근당홀딩스",
    "대상",
    "대상1우",
    "신영증권",
    "신영증권1우",
    "SK네트웍스",
    "SK네트웍스1우",
    "한양증권",
    "한양증권1우",
    "신화다이나믹스",
    "알루코",
    "대한제당",
    "대한제당1우",
    "오리온홀딩스",
    "삼화콘덴서공업",
    "디엘건설",
    "KISCO홀딩스",
    "코오롱",
    "코오롱1우",
    "아세아",
    "비비안",
    "경농",
    "고려산업",
    "도화엔지니어링",
    "삼양통상",
    "한국수출포장공업",
    "동성제약",
    "한일철강",
    "고려제강",
    "롯데푸드",
    "아세아제지",
    "한진",
    "넥센타이어",
    "넥센타이어1우",
    "SH에너지화학",
    "케이씨씨",
    "한독",
    "범양건영",
    "세기상사",
    "삼익악기",
    "화성산업",
    "원림",
    "디비손해보험",
    "에스엘",
    "휴니드테크놀러지스",
    "대한해운",
    "삼성전자",
    "삼성전자1우",
    "NH투자증권",
    "NH투자증권1우",
    "이수화학",
    "동부건설",
    "동부건설1우",
    "동원산업",
    "화승인더스트리",
    "사조오양",
    "삼아알미늄",
    "에스케이디스커버리",
    "에스케이디스커버리1우",
    "한국전자홀딩스",
    "제주은행",
    "LS",
    "녹십자",
    "대원전선",
    "대원전선1우",
    "지에스건설",
    "대구백화점",
    "카프로",
    "한일현대시멘트",
    "삼성SDI",
    "삼성SDI1우",
    "인스코비",
    "대림통상",
    "대한유화",
    "삼성공조",
    "영풍제지",
    "미래에셋증권",
    "미래에셋증권1우",
    "에이케이홀딩스",
    "신송홀딩스",
    "태경케미컬",
    "우성",
    "지에스리테일",
    "일신석재",
    "미래아이앤지",
    "사조산업",
    "벽산",
    "한국특강",
    "오뚜기",
    "디티알오토모티브",
    "에이프로젠메디신",
    "샘표",
    "일양약품",
    "일양약품1우",
    "동방아그로",
    "선도전기",
    "폴루스바이오팜",
    "이수페타시스",
    "국도화학",
    "에프앤에프홀딩스",
    "코리아써키트",
    "코리아써키트1우",
    "서연",
    "태평양물산",
    "사조동아원",
    "대덕",
    "대동전자",
    "이건산업",
    "엔아이스틸",
    "조흥",
    "제일파마홀딩스",
    "오리엔트바이오",
    "신일전자",
    "티씨씨스틸",
    "국제약품",
    "보락",
    "진흥기업",
    "진흥기업1우",
    "진흥기업2우",
    "아모레퍼시픽그룹",
    "아모레퍼시픽그룹1우",
    "삼영무역",
    "선앤엘",
    "미원상사",
    "신풍제지",
    "대유에이텍",
    "티와이엠",
    "유성기업",
    "한국쉘석유",
    "금호건설",
    "금호건설1우",
    "부광약품",
    "혜인",
    "세아제강지주",
    "에이프로젠제약",
    "코오롱글로벌",
    "코오롱글로벌1우",
    "성보화학",
    "대웅",
    "일성신약",
    "디아이",
    "일신방직",
    "대원제약",
    "삼양식품",
    "태광산업",
    "흥아해운",
    "한일홀딩스",
    "한국화장품제조",
    "쌍용씨앤이",
    "유화증권",
    "유화증권1우",
    "유안타증권",
    "유안타증권1우",
    "한진중공업홀딩스",
    "대한항공",
    "대한항공1우",
    "영진약품",
    "한화투자증권",
    "한화투자증권1우",
    "대신증권",
    "대신증권1우",
    "대신증권2우",
    "LG",
    "LG1우",
    "아이에이치큐",
    "에스앤티중공업",
    "넥스트사이언스",
    "방림",
    "쌍용자동차",
    "미창석유공업",
    "포스코케미칼",
    "한성기업",
    "코리안리재보험",
    "삼영화학공업",
    "진양산업",
    "대한화섬",
    "보령제약",
    "남양유업",
    "남양유업1우",
    "사조대림",
    "롯데정밀화학",
    "현대제철",
    "에스지세계물산",
    "신흥",
    "한국석유공업",
    "태양금속공업",
    "태양금속공업1우",
    "동방",
    "한솔홀딩스",
    "신세계",
    "엔피씨",
    "엔피씨1우",
    "남성",
    "현대약품",
    "세방",
    "세방1우",
    "농심",
    "삼익THK",
    "서울식품공업",
    "서울식품공업1우",
    "송원산업",
    "삼화왕관",
    "세방전지",
    "깨끗한나라",
    "깨끗한나라1우",
    "현대비앤지스틸",
    "현대비앤지스틸1우",
    "삼천리",
    "조광피혁",
    "한솔테크닉스",
    "팜젠사이언스",
    "써니전자",
    "효성",
    "덕성",
    "덕성1우",
    "DRB동일",
    "티웨이홀딩스",
    "동일산업",
    "조광페인트",
    "씨아이테크",
    "한신공영",
    "신라교역",
    "성신양회",
    "성신양회1우",
    "롯데지주",
    "휴스틸",
    "부산주공",
    "코스모신소재",
    "에스지씨에너지",
    "한창",
    "빙그레",
    "녹십자홀딩스",
    "녹십자홀딩스2우",
    "롯데칠성음료",
    "롯데칠성음료1우",
    "국동",
    "모나미",
    "현대자동차",
    "현대자동차1우",
    "현대자동차2우",
    "현대자동차3우",
    "신성통상",
    "코스모화학",
    "한국공항",
    "현대그린푸드",
    "포스코",
    "삼진제약",
    "에스피씨삼립",
    "삼영전자공업",
    "파미셀",
    "넥센",
    "넥센1우",
    "크라운해태홀딩스",
    "크라운해태홀딩스1우",
    "대림비앤코",
    "신영와코루",
    "풍산홀딩스",
    "제이콘텐트리",
    "한국가스공사",
    "에스앤티홀딩스",
    "엔씨소프트",
    "팜스코",
    "와이지플러스",
    "엘지헬로비전",
    "광주신세계",
    "하나투어",
    "키움증권",
    "상신브레이크",
    "남선알미늄",
    "남선알미늄1우",
    "문배철강",
    "서흥",
    "일정실업",
    "메리츠증권",
    "윌비스",
    "아남전자",
    "율촌화학",
    "호텔신라",
    "호텔신라1우",
    "금비",
    "한미사이언스",
    "동양철관",
    "케이씨티시",
    "경인전자",
    "삼성전기",
    "삼성전기1우",
    "심팩",
    "한솔로지스틱스",
    "대양금속",
    "무림페이퍼",
    "한샘",
    "신원",
    "신원1우",
    "광동제약",
    "참엔지니어링",
    "대우전자부품",
    "태영건설",
    "태영건설1우",
    "한올바이오파마",
    "케이씨그린홀딩스",
    "경동나비엔",
    "한창제지",
    "삼화전기",
    "한국조선해양",
    "무림피앤피",
    "모토닉",
    "삼정펄프",
    "플레이그램",
    "한화솔루션",
    "한화솔루션1우",
    "영원무역홀딩스",
    "한국내화",
    "우리종합금융",
    "오씨아이",
    "한국프랜지공업",
    "엘에스일렉트릭",
    "고려아연",
    "삼성중공업",
    "삼성중공업1우",
    "한솔PNS",
    "지코",
    "웰바이오텍",
    "현대미포조선",
    "진양폴리우레탄",
    "화천기계",
    "화신",
    "평화홀딩스",
    "아이에스동서",
    "퍼스텍",
    "S-OIL",
    "S-OIL1우",
    "삼호개발",
    "진원생명과학",
    "LG이노텍",
    "에넥스",
    "CJ씨푸드",
    "CJ씨푸드1우",
    "롯데케미칼",
    "에이치엠엠",
    "현대위아",
    "삼화전자공업",
    "태림포장",
    "성안",
    "유니켐",
    "부산산업",
    "갤럭시아 에스엠",
    "한농화성",
    "와이투솔루션",
    "한신기계공업",
    "현대코퍼레이션",
    "금호석유화학",
    "금호석유화학1우",
    "SKC",
    "STX",
    "신성이엔지",
    "디비아이엔씨",
    "영흥",
    "아센디오",
    "계양전기",
    "계양전기1우",
    "영화금속",
    "경동인베스트",
    "현대모비스",
    "한화에어로스페이스",
    "더존비즈온",
    "센트럴인사이트",
    "경인양행",
    "에이치디씨",
    "모나리자",
    "에스원",
    "대창",
    "세우글로벌",
    "일성건설",
    "화승코퍼레이션",
    "디와이",
    "계룡건설산업",
    "까뮤이앤씨",
    "지엠비코리아",
    "지누스",
    "한익스프레스",
    "대영포장",
    "금강공업",
    "금강공업1우",
    "영보화학",
    "극동유화",
    "태경비케이",
    "한솔케미칼",
    "사조씨푸드",
    "한라",
    "동원시스템즈",
    "동원시스템즈1우",
    "유니드",
    "성문전자",
    "성문전자1우",
    "인디에프",
    "이스타코",
    "대창단조",
    "에이엔피",
    "부산도시가스",
    "예스코홀딩스",
    "쎌마테라퓨틱스",
    "큐로",
    "한국전력공사",
    "일진홀딩스",
    "태경산업",
    "대현",
    "삼성증권",
    "케이지동부제철 주식회사",
    "케이지동부제철 주식회사1우",
    "한세예스24홀딩스",
    "환인제약",
    "신대양제지",
    "디비금융투자",
    "대성홀딩스",
    "퍼시스",
    "웅진",
    "광명전기",
    "명문제약",
    "우신시스템",
    "서울도시가스",
    "수산중공업",
    "SK텔레콤",
    "현대엘리베이터",
    "풀무원",
    "광전자",
    "E1",
    "한국카본",
    "삼성에스디에스",
    "조일알미늄",
    "동원금속",
    "SK가스",
    "한온시스템",
    "신풍제약",
    "신풍제약1우",
    "티에이치엔",
    "세아특수강",
    "하이트론씨스템즈",
    "대교",
    "대교 1우",
    "한섬",
    "키다리스튜디오",
    "일진머티리얼즈",
    "아시아나항공",
    "일진디스플레이",
    "서원",
    "코웨이주식회사",
    "세원정공",
    "삼원강재",
    "MH에탄올",
    "한국종합기술",
    "동남합성",
    "롯데쇼핑",
    "다우기술",
    "인지컨트롤스",
    "인팩",
    "에쓰씨엔지니어링",
    "위스컴",
    "디씨엠",
    "중소기업은행",
    "한국콜마홀딩스",
    "대원화성",
    "덕양산업",
    "KPX케미칼",
    "에스제이엠홀딩스",
    "한국단자공업",
    "미래산업",
    "제이준코스메틱",
    "한솔홈데코",
    "이구산업",
    "남해화학",
    "한국주강",
    "스틱인베스트먼트",
    "부국철강",
    "동서",
    "마니커",
    "세하",
    "삼성엔지니어링",
    "동아지질",
    "팬오션",
    "케이씨",
    "신도리코",
    "삼성카드",
    "제일기획",
    "케이티",
    "케이티비투자증권",
    "교보증권",
    "동원수산",
    "비케이탑스",
    "신세계인터내셔날",
    "신세계푸드",
    "콤텍시스템",
    "롯데관광개발",
    "황금에스티",
    "LG유플러스",
    "삼성생명보험",
    "케이에이치필룩스",
    "자화전자",
    "체시스",
    "한국유나이티드제약",
    "세종공업",
    "케이티앤지",
    "무학",
    "두산중공업",
    "에스비에스",
    "LG디스플레이",
    "신세계건설",
    "NICE홀딩스",
    "인천도시가스",
    "SK",
    "한국토지신탁",
    "지투알",
    "백산",
    "강원랜드",
    "네이버",
    "신세계아이앤씨",
    "카카오",
    "대우건설",
    "포스코인터내셔널",
    "유니온머티리얼",
    "한국항공우주산업",
    "동원에프앤비",
    "우진플라임",
    "한전KPS",
    "진양화학",
    "LG생활건강",
    "LG생활건강1우",
    "LG화학",
    "LG화학1우",
    "한국전력기술",
    "케이티스카이라이프",
    "한미글로벌건축사사무소",
    "테이팩스",
    "신한금융지주회사",
    "현대홈쇼핑",
    "포스코강판",
    "세아홀딩스",
    "다스코",
    "케이티씨에스",
    "케이티아이에스",
    "한라홀딩스",
    "LG전자",
    "LG전자1우",
    "세이브존아이앤씨",
    "종근당바이오",
    "에스앤티모티브",
    "대우조선해양",
    "현대두산인프라코어",
    "한미반도체",
    "주연테크",
    "케이에스에스해운",
    "코스맥스비티아이",
    "웅진씽크빅",
    "한국월드와이드베트남부동산개발특별자산1호투자회사",
    "제이더블유홀딩스",
    "SK이노베이션",
    "SK이노베이션1우",
    "한진중공업",
    "엠씨넥스",
    "씨제이제일제당",
    "씨제이제일제당1우",
    "비상교육",
    "진양홀딩스",
    "에스앤티에너지",
    "SBS미디어홀딩스",
    "인바이오젠",
    "해태제과식품",
    "동성케미컬",
    "쌍방울",
    "셀트리온",
    "삼성출판사",
    "에스케이렌터카",
    "휴켐스",
    "대호에이엘",
    "대웅제약",
    "한세엠케이",
    "디에스알제강",
    "현대백화점",
    "용평리조트",
    "한국투자금융지주",
    "한국투자금융지주1우",
    "하이스틸",
    "한국지역난방공사",
    "롯데하이마트",
    "코아스",
    "STX중공업",
    "유엔젤",
    "농심홀딩스",
    "금호타이어",
    "이엔플러스",
    "새론오토모티브",
    "세진중공업",
    "유니퀘스트",
    "STX엔진",
    "텔코웨어",
    "에이블씨엔씨",
    "지에스",
    "지에스1우",
    "씨제이씨지브이",
    "현대리바트",
    "휴비스",
    "일진다이아몬드",
    "휠라홀딩스",
    "동양생명보험",
    "HSD엔진",
    "그린케미칼",
    "대한제강",
    "동양고속",
    "이월드",
    "대상홀딩스",
    "대상홀딩스1우",
    "티비에이치글로벌",
    "엔케이",
    "미래에셋생명보험",
    "현대글로비스",
    "하나금융지주",
    "한화생명보험",
    "진도",
    "맥쿼리한국인프라투융자회사",
    "HDC현대EP",
    "제주항공",
    "평화산업",
    "노루페인트",
    "노루페인트1우",
    "메타랩스",
    "아모레퍼시픽",
    "아모레퍼시픽1우",
    "세원이앤씨",
    "티웨이항공",
    "디아이씨",
    "케이이씨",
    "KPX홀딩스",
    "기신정기",
    "LF",
    "이아이디",
    "형지엘리트",
    "후성",
    "효성ITX",
    "미래에셋맵스아시아퍼시픽부동산공모1호투자회사",
    "우진",
    "미원홀딩스",
    "LX하우시스",
    "LX하우시스1우",
    "컨버즈",
    "영원무역",
    "그랜드코리아레저",
    "락앤락",
    "대성에너지",
    "우리들휴브레인",
    "케이씨코트렐",
    "조선선재",
    "코오롱인더스트리",
    "코오롱인더스트리1우",
    "아이마켓코리아",
    "한국화장품",
    "에스제이엠",
    "현대퓨처넷",
    "대성산업",
    "한미약품",
    "인터지스",
    "한전산업개발",
    "미원화학",
    "시디즈",
    "선진",
    "다이나믹디자인",
    "케이탑자기관리부동산투자회사",
    "덴티움",
    "삼양사",
    "삼양사1우",
    "한국투자ANKOR유전해외자원개발특별자산투자회사1호(지분증권)",
    "하이골드오션3호선박투자회사",
    "디에스알",
    "메리츠금융지주",
    "코오롱플라스틱",
    "BNK금융지주",
    "DGB금융지주",
    "이마트",
    "에이자기관리부동산투자회사",
    "이연제약",
    "풍산",
    "일진전기",
    "한국철강",
    "KB금융지주",
    "한세실업",
    "바다로19호선박투자회사",
    "애경케미칼",
    "한국타이어앤테크놀로지",
    "한국콜마",
    "동일고무벨트",
    "한국투자패러랠유전해외자원개발특별자산투자회사1호지분증권",
    "엘브이엠씨홀딩스",
    "동아에스티",
    "현대로템",
    "엘아이지넥스원",
    "코리아써키트2우",
    "JB금융지주",
    "한진칼",
    "한진칼1우",
    "엔에이치엔",
    "아세아시멘트",
    "종근당",
    "화인베스틸",
    "비지에프",
    "더블유게임즈",
    "코스맥스",
    "쿠쿠홀딩스",
    "서연이화",
    "씨에스윈드",
    "엔에스쇼핑",
    "피아이첨단소재",
    "삼성물산",
    "만도",
    "모두투어자기관리부동산투자회사",
    "디와이파워",
    "한솔제지",
    "에스케이디앤디",
    "이노션",
    "경보제약",
    "금호에이치티",
    "토니모리",
    "에이제이네트웍스",
    "제이에스코퍼레이션",
    "에이치디씨랩스",
    "동일제강",
    "SK1우",
    "잇츠한불",
    "삼성물산1우",
    "해성디에스",
    "현대코퍼레이션홀딩스",
    "제이더블유생명과학",
    "삼일씨엔에스",
    "한국자산신탁",
    "두올",
    "동양피스톤",
    "호전실업",
    "엘에스전선아시아",
    "두산밥캣",
    "샘표식품",
    "핸즈코퍼레이션",
    "일동제약",
    "삼성바이오로직스",
    "화승엔터프라이즈",
    "한화3우",
    "넷마블",
    "크래프톤",
    "이리츠코크렙기업구조조정부동산투자회사",
    "애경산업",
    "크라운제과(신설)",
    "크라운제과(신설)1우",
    "현대중공업지주",
    "현대일렉트릭앤에너지시스템",
    "현대건설기계",
    "경동도시가스(신설)",
    "미원스페셜티케미칼(신설)",
    "오리온(신설)",
    "제일약품(신설)",
    "아시아나아이디티",
    "일진하이솔루스",
    "삼양패키징",
    "우진아이엔에스",
    "진에어",
    "롯데제과(신설)",
    "롯데지주1우",
    "비지에프리테일(신설)",
    "동아타이어공업(신설)",
    "케이씨텍",
    "쿠쿠홈시스",
    "SK케미칼",
    "SK케미칼 1우",
    "엔에이치프라임위탁관리부동산투자회사",
    "두산퓨얼셀보통주",
    "두산퓨얼셀1우선주",
    "두산퓨얼셀2우선주(신형)",
    "솔루스첨단소재",
    "솔루스첨단소재1우",
    "솔루스첨단소재2우",
    "이지스밸류플러스위탁관리부동산투자회사",
    "아모레퍼시픽그룹 3우",
    "SK바이오팜",
    "롯데위탁관리부동산투자회사",
    "한화시스템",
    "현대에너지솔루션(주)",
    "씨제이4우",
    "자이에스앤디(주)",
    "센트랄모텍",
    "우리금융지주",
    "에스케이바이오사이언스",
    "대덕1우",
    "현대오토에버",
    "솔루엠",
    "에어부산",
    "세아제강(신설)",
    "한일시멘트(신설)",
    "효성화학",
    "효성티앤씨",
    "효성중공업",
    "효성첨단소재",
    "드림텍",
    "신한알파위탁관리부동산투자회사",
    "에이치디씨현대산업개발",
    "하나제약",
    "미래에셋증권2우",
    "롯데정보통신",
    "카카오뱅크",
    "케이씨씨글라스",
    "에이플러스에셋어드바이저",
    "교촌에프앤비",
    "제이알글로벌위탁관리부동산투자회사",
    "이지스레지던스위탁관리부동산투자회사",
    "하이브",
    "대덕전자",
    "대덕전자 1우",
    "명신산업",
    "코람코에너지플러스위탁관리부동산투자회사",
    "미래에셋맵스제1호위탁관리부동산투자회사",
    "티와이홀딩스",
    "티와이홀딩스1우",
    "이에스알켄달스퀘어위탁관리부동산투자회사",
    "에스디바이오센서",
    "프레스티지바이오파마 KDR",
    "디엘이앤씨",
    "디엘이앤씨 1우",
    "한컴라이프케어",
    "엔에이치기업인수목적19호",
    "롯데렌탈(주)",
    "화승알앤에이",
    "아주스틸",
    "현대중공업",
    "에스케이아이이테크놀로지",
    "카카오페이",
    "에프앤에프(신설)",
    "엘엑스홀딩스",
    "엘엑스홀딩스1우",
    "디앤디플랫폼위탁관리부동산투자회사",
    "SK스퀘어",
    "에스케이위탁관리부동산투자회사",
    "엔에이치올원위탁관리부동산투자회사",
    "케이카",
    "미래에셋글로벌위탁관리부동산투자회사",
    "신한서부티엔디위탁관리부동산투자회사",
]

# if __name__ == "__main__":

@logging_time
def run():
    
    # pool = Pool(4)
    # m = Manager()

    # title_list = m.list()
    # url_list = m.list()
    # result_dict = m.dict()

    # tuple_list = m.list()
    # tuple_list.append(('title','pov_neg'))

    # process = multiprocessing.cpu_count() * 2
    # # # print(company)
    # with Pool(processes=process) as pool:
    #     pool.starmap(
    #         search_crawl, [(posneg, positive,tuple_list, query) for query in cospi[:5]] ###### 크롤링 함수 사용시
    #         # api_search, [(tuple_list, query) for query in cospi] ###### api 함수 사용시
    #     )
    #     pool.close()
    #     pool.join()

    tuple_list = list()
    tuple_list.append(('title','label','company'))
    for query in cospi[101:200]:
        search_crawl(tuple_list, query)


    return tuple_list



if __name__ == "__main__":
    tuple = run()
    with open('./train.csv', 'w') as f:
        writer = csv.writer(f , lineterminator='\n')
        for tup in tuple:
            writer.writerow(tup)