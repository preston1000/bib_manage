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
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('table/', views.table, name='table'),
    path('net/', views.net, name='net'),
    path('sample-data/', views.get_sample_data, name='sample-data'),
    path('about/vis-data/', views.get_vis_data, name='vis-data'),
    path('demo/table/user/', views.get_author_table_data, name='author-table-data'),
    path('add-pub/', views.add_publication, name='add-pub'),
    path('search-pub/', views.search_publication, name='search-pub'),
    path('revise-pub/', views.revise_publication, name='revise-pub'),
    path('edit-pub/', views.get_pib_info_for_edit, name='edit-pub'),
    path('verify/', views.verify_auth, name='verify_auth'),
    path('pub-interface/', views.pub_interface, name='pub-interface'),
    path('upload-bib/', views.upload_bib_add_record, name='upload-bib'),
    path('split-name/', views.split_name, name='split-name'),
    path('search-pub-popup/', views.search_pub_popup, name='search-pub-popup'),
]
