import os

from django.contrib import messages
from django.contrib.auth import (
    login,
    logout,
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    VideoForm,
    ReelUploadForm,
)
from .models import Video, Reel, ReelRating
from .utils import (
    download_youtube_video,
    create_video_reels,
    extract_key_moments_with_labels,
    get_youtube_transcript,
)


User = get_user_model()


def index(request):
	return render(
        request,
        'web_app/index.html',
    )


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/web_app/index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'web_app/register.html', {'form': form})


def login_view(request):
    form = CustomAuthenticationForm()

    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                login(request, user)
                
                # Redirect based on role
                if user.role == 'Student':
                    return redirect('/web_app/student_dashboard/')
                elif user.role == 'Instructor':
                    return redirect('/web_app/instructor_dashboard/')
                else:
                    return redirect('/')  # Fallback if no role is defined
        else:
            print("Form errors:", form.errors)  # Debugging errors

    return render(request, 'web_app/login.html', {'form': form})


def logout_view(request):
    logout(request)  # Logs out the user
    return redirect('/web_app/index')  # Redirect to the index page


@login_required
def student_dashboard_view(request):
    """Student dashboard where students can select videos and view their reels."""
    videos = request.user.allowed_videos.all()  # ✅ Only assigned videos

    selected_video = None
    reels = None

    if request.method == "POST":
        video_id = request.POST.get("selected_video")
        if video_id:
            selected_video = get_object_or_404(Video, video_id=video_id)
            reels = selected_video.reels.all()

    return render(
        request,
        'web_app/student_dashboard.html',
        {
            'videos': videos,
            'selected_video': selected_video,
            'reels': reels
        }
    )


@login_required
def instructor_dashboard_view(request):
    User = get_user_model()

    if request.method == 'POST':
        print("POST data received:", dict(request.POST))

        if "assign_video" in request.POST:
            video_id = request.POST.get("video_id")
            student_ids = request.POST.getlist("students")

            try:
                video = get_object_or_404(Video, video_id=video_id, user=request.user)
                students = User.objects.filter(id__in=student_ids)

                for student in students:
                    print(type(student))
                    print(f"Assigning {video} to {student}")
                    student.allowed_videos.add(video)
                    
                messages.success(request, "✅ Video assigned successfully.")
            except Exception as e:
                messages.error(request, f"❌ Failed to assign video: {str(e)}")

            return redirect("instructor_dashboard")

        else:
            form = VideoForm(request.POST)
            if form.is_valid():
                url = form.cleaned_data['url']
                video_id = url.split("v=")[1].split("&")[0]

                video, created = Video.objects.get_or_create(
                    user=request.user,
                    video_id=video_id,
                    url=url
                )

                if created:
                    download_youtube_video(url, video)
                    messages.success(request, "🎬 Video uploaded and downloading started.")
                else:
                    messages.info(request, "ℹ️ Video already exists.")

                return redirect("instructor_dashboard")

    else:
        form = VideoForm()

    videos = Video.objects.filter(user=request.user).prefetch_related('reels')
    students = User.objects.filter(is_staff=False, is_superuser=False).exclude(id=request.user.id)

    return render(request, 'web_app/instructor_dashboard.html', {
        'form': form,
        'videos': videos,
        'students': students,
    })


@login_required
def profile_view(request):
    return render(request, 'web_app/profile.html')


@login_required
def generate_reels_view(request, video_id):
    """Generate reels with OpenAI descriptions and embed summaries into the videos."""
    
    video = get_object_or_404(Video, video_id=video_id, user=request.user)

    video.status = "Downloading Video"
    video.save(update_fields=["status"])
    
    force_regenerate = request.GET.get("force", "false").lower() == "true"
    if not force_regenerate and video.reels.exists():
        return JsonResponse({"success": False, "message": "Reels are already generated."})

    try:
        num_reels_requested = int(request.GET.get("num_reels", 3))

        video.status = "Processing with OpenAI"
        video.save(update_fields=["status"])

        key_moments = extract_key_moments_with_labels(
            get_youtube_transcript(video.video_id),
            num_reels_requested
        )

        if not key_moments:
            video.status = "Failed: No Key Moments Found"
            video.save(update_fields=["status"])
            return JsonResponse({"success": False, "message": "No key moments detected from OpenAI."})

        num_reels = min(len(key_moments), num_reels_requested)
        reel_durations = [(moment["end_time"] - moment["start_time"]) for moment in key_moments]

        if force_regenerate:
            video.reels.all().delete()

        video.status = "Creating Reels"
        video.save(update_fields=["status"])

        create_video_reels(
            video.file_path.path,
            video,
            key_moments[:num_reels],
            num_reels,
            reel_durations[:num_reels]
        )

        video.status = "Complete"
        video.save(update_fields=["status"])

        return JsonResponse({"success": True, "message": "Reels generated successfully with summaries!"})

    except Exception as e:
        video.status = "Failed"
        video.save(update_fields=["status"])
        return JsonResponse({"success": False, "message": f"Error generating reels: {str(e)}"})


@login_required
def get_video_status(request, video_id):
    """Returns the processing status of a video."""
    video = get_object_or_404(Video, video_id=video_id, user=request.user)
    return JsonResponse({"status": video.status})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            return JsonResponse({'success': True, 'message': "Your password has been updated successfully!"})
        else:
            errors = [error for field_errors in form.errors.values() for error in field_errors]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    
    return JsonResponse({'success': False, 'errors': ["Invalid request."]}, status=400)


@login_required
def get_reels_view(request, video_id):
    """Return reels data for displaying in modal."""
    reels = Reel.objects.filter(video__video_id=video_id).order_by("file_path")

    reels_data = [
        {
            "id": reel.id,
            "file_path": reel.file_path.url,  # ✅ Include file path
            "start_time": reel.start_time,
            "end_time": reel.end_time,
            "label": reel.label,
            "labels": [reel.label],  # Placeholder for multiple labels per reel
            "average_rating": reel.average_rating,  # ✅ Send average rating
            "total_votes": reel.ratings.count(),  # ✅ Send total number of ratings
        }
        for reel in reels
    ]

    return JsonResponse({"success": True, "reels": reels_data})


@login_required
def update_reels_view(request, video_id):
    """Update reel data after instructor edits."""
    if request.method == "POST":
        reels = Reel.objects.filter(video__video_id=video_id)

        for reel in reels:
            reel_id = str(reel.id)

            reel.label = request.POST.get(f"title_{reel_id}", reel.label)
            reel.start_time = float(request.POST.get(f"start_{reel_id}", reel.start_time))
            reel.end_time = float(request.POST.get(f"end_{reel_id}", reel.end_time))

            labels = request.POST.get(f"labels_{reel_id}", "").split(", ")
            reel.label = labels[0]  # Assign first label as primary title

            reel.save()

        return JsonResponse({"success": True, "message": "Reels updated successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request."})


@login_required
def rate_reel(request, reel_id, rating):
    """Allow users to rate a reel (0-5 stars)."""
    reel = get_object_or_404(Reel, id=reel_id)

    # Store or update the rating (ensures each user can only rate once)
    user_rating, created = ReelRating.objects.update_or_create(
        user=request.user,
        reel=reel,
        defaults={"rating": rating}
    )

    # ✅ Calculate the new average rating and total votes
    ratings_data = reel.ratings.aggregate(avg_rating=Avg("rating"), total_votes=Count("rating"))

    average_rating = ratings_data["avg_rating"] or 0
    total_votes = ratings_data["total_votes"] or 0

    # ✅ Update the Reel model with the new rating stats
    reel.average_rating = average_rating
    reel.save(update_fields=["average_rating"])

    return JsonResponse({
        "success": True,
        "new_average_rating": round(average_rating, 1),
        "total_votes": total_votes
    })


@login_required
def remove_reel_rating_view(request, reel_id):
    """Allow users to remove their rating from a reel."""
    reel = get_object_or_404(Reel, id=reel_id)

    # ✅ Delete user's rating if it exists
    ReelRating.objects.filter(user=request.user, reel=reel).delete()

    # ✅ Recalculate the average rating and total votes
    ratings_data = reel.ratings.aggregate(avg_rating=Avg("rating"), total_votes=Count("rating"))

    average_rating = ratings_data["avg_rating"] or 0
    total_votes = ratings_data["total_votes"] or 0

    # ✅ Update Reel model with new rating data
    reel.average_rating = average_rating
    reel.save(update_fields=["average_rating"])

    return JsonResponse({
        "success": True,
        "new_average_rating": round(average_rating, 1),
        "total_votes": total_votes
    })


@login_required
def search_videos_reels_view(request):
    query = request.GET.get("query", "").strip()
    if not query:
        return JsonResponse({"success": False, "message": "No search query provided."})

    # Search in both videos and reels
    videos = Video.objects.filter(title__icontains=query)
    reels = Reel.objects.filter(label__icontains=query)

    # Convert results to JSON format
    video_results = [
        {"id": video.id, "title": video.title, "video_id": video.video_id}
        for video in videos
    ]

    reel_results = [
        {
            "id": reel.id,
            "label": reel.label,
            "file_path": reel.file_path.url,
            "video_id": reel.video.video_id,
            "average_rating": reel.average_rating,
            "total_votes": reel.total_votes,
        }
        for reel in reels
    ]

    return JsonResponse({"success": True, "videos": video_results, "reels": reel_results})


@login_required
def delete_video_view(request, video_id):
    """Delete a video along with all its associated reels."""
    video = get_object_or_404(Video, video_id=video_id, user=request.user)

    # Delete all associated reels and files
    for reel in video.reels.all():
        if reel.file_path:
            if os.path.exists(reel.file_path.path):
                os.remove(reel.file_path.path)  # Delete reel file
        reel.delete()

    # Delete the video file if it exists
    if video.file_path:
        if os.path.exists(video.file_path.path):
            os.remove(video.file_path.path)

    # Delete video from database
    video.delete()

    return JsonResponse({"success": True, "message": "Video deleted successfully!"})


@login_required
def delete_reel_view(request, reel_id):
    """Delete a specific reel."""
    reel = get_object_or_404(Reel, id=reel_id, video__user=request.user)

    # Delete the reel file if it exists
    if reel.file_path:
        if os.path.exists(reel.file_path.path):
            os.remove(reel.file_path.path)

    reel.delete()

    return JsonResponse({"success": True, "message": "Reel deleted successfully!"})


@login_required
def manual_reel_upload(request, video_id):
    video = get_object_or_404(Video, video_id=video_id, user=request.user)

    if request.method == "POST":
        form = ReelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            reel = form.save(commit=False)
            reel.video = video
            reel.save()
            return redirect("web_app/index")  # or wherever you want
    else:
        form = ReelUploadForm()

    return render(request, "web_app/manual_reel_upload.html", {"form": form, "video": video})


@login_required
def assign_video_view(request):
    """Assign a video to a student (via POST with user_id and video_id)."""
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        video_id = request.POST.get("video_id")

        try:
            user = User.objects.get(id=user_id, role="Student")
            video = Video.objects.get(id=video_id)
            user.allowed_videos.add(video)
            return JsonResponse({"success": True, "message": "Video assigned successfully!"})
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "Student not found."})
        except Video.DoesNotExist:
            return JsonResponse({"success": False, "message": "Video not found."})
    
    return JsonResponse({"success": False, "message": "Invalid request method."})

