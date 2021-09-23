"""webs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import pages.views as views


urlpatterns = [
    path('', views.index, name='home'),  # home page
    path('admin/', admin.site.urls),
    path('about/', views.about, name='about'),
    path('about2/', views.about2, name='about'),
    path('table/', views.table, name='table'),
    path('net/', views.net, name='net'),
    path('sample-data/', views.get_sample_data, name='sample-data'),
    path('about/vis-data/', views.get_vis_data, name='vis-data'),
    path('demo/table/user/', views.get_author_table_data, name='author-table-data'),
    path('add-pub/', views.add_publication, name='add-pub'),
    path('add-person/', views.add_person, name='add-person'),
    path('add-venue/', views.add_venue, name='add-venue'),
    path('add-relation/', views.add_relation, name='add-relation'),
    path('search-pub/', views.search_publication, name='search-pub'),
    path('search-person/', views.search_person, name='search-person'),
    path('search-venue/', views.search_venue, name='search-venue'),
    path('revise-pub/', views.revise_publication, name='revise-pub'),
    path('revise-person/', views.revise_person, name='revise-person'),
    path('revise-venue/', views.revise_venue, name='revise-venue'),
    path('edit-pub/', views.get_pib_info_for_edit, name='edit-pub'),
    path('verify/', views.verify_auth, name='verify_auth'),
    path('pub-interface/', views.pub_interface, name='pub-interface'),
    path('upload-bib/', views.upload_bib_add_record, name='upload-bib'),
    path('split-name/', views.split_name, name='split-name'),
    path('search-pub-popup/', views.search_pub_popup, name='search-pub-popup'),
    path('search-person-popup/', views.search_person_popup, name='search-person-popup'),
    path('search-venue-popup/', views.search_venue_popup, name='search-venue-popup'),

    path('home/', views.search_home, name="search-home"),  # 搜索文献页面
    path('search/', views.search_result, name="search"),  # 搜索结果页面
    path('search/view-pdf/', views.view_pdf, name="search-view-pdf"),  # 浏览pdf页面， todo
    path('manage/', views.manage, name="manage"),  # 三元组检查和编辑界面 todo

    path('search/result/', views.search_publication_new, name="search-result"),  # 查询结果（详细）
    path('search/search-count/', views.search_publication_count, name="search-result-count"),  # 查询结果（个数）
    path('search/show-pdf/', views.show_pdf, name="search-show-pdf"),  # 浏览pdf， todo
    # path('manage/match-pub', views.manage_match_pub, name="manage-match-pub")

    # 意图理解相关网址
    path('deprel/', views.deprel, name="deprel"),  # 依存分析网页界面
    path('deprel/save-result/', views.save_deprel_result, name="deprel-result"),  # 保存评论结果
    path('deprel/resolve-deprel/', views.resolve_deprel, name="resolve-deprel"),  # 解析句子依存关系的接口
    path('tu/', views.command_resolve, name="resolve-command"),  # 解析任务型指令

    # 火车相关
    path('getCoordinates/', views.resolve_coordinates, name="resolve_coordinates"),  # 上传车站信息（excel文件）进行解析
    path('parseExcelStations/', views.parse_excel_stations, name="parse_excel_stations"),  # 解析excel

]
