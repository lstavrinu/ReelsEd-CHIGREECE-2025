
from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^index/$', views.index, name='index'),
	re_path(r'^login/$', views.login_view, name='login'),
    re_path(r'^logout/$', views.logout_view, name='logout'),
    re_path(r'^register/$', views.register_view, name='register'),
	re_path(r'^student_dashboard/$', views.student_dashboard_view, name='student_dashboard'),
    re_path(r'^instructor_dashboard/$', views.instructor_dashboard_view, name='instructor_dashboard'),
    re_path(r'^generate_reels/(?P<video_id>[\w-]+)/$', views.generate_reels_view, name='generate_reels'),
    re_path(r'^profile/$', views.profile_view, name='profile'),
    re_path(r'^profile/change_password/$', views.change_password_view, name='change_password'),
	re_path(r'^get_reels/(?P<video_id>[^/]+)/$', views.get_reels_view, name='get_reels'),
    re_path(r'^update_reels/(?P<video_id>[^/]+)/$', views.update_reels_view, name='update_reels'),
    re_path(r'^generate_reels/(?P<video_id>[^/]+)/$', views.generate_reels_view, name='generate_reels'),
    re_path(r'^get_video_status/(?P<video_id>[\w-]+)/$', views.get_video_status, name='get_video_status'),
 	re_path(r'^search/$', views.search_videos_reels_view, name='search_videos_reels'),
	re_path(r"^rate_reel/(?P<reel_id>\d+)/(?P<rating>\d+)/$", views.rate_reel, name="rate_reel"),
    re_path(r"^remove_reel_rating/(?P<reel_id>\d+)/$", views.remove_reel_rating_view, name="remove_reel_rating"),
    re_path(r"^delete_video/(?P<video_id>[a-zA-Z0-9_-]+)/$", views.delete_video_view, name="delete_video"),
    re_path(r"^delete_reel/(?P<reel_id>\d+)/$", views.delete_reel_view, name="delete_reel"),
	re_path(r"^assign_video/$", views.assign_video_view, name="assign_video"),
	re_path(r'^manual_upload/(?P<video_id>[\w-]+)/$', views.manual_reel_upload, name="manual_reel_upload"),
]
