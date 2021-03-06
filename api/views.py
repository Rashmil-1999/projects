from django.shortcuts import render, HttpResponse
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, action
from rest_framework import viewsets, status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from .models import *
from .utility import generate_csv, month_dict, get_dates
from .render import render_to_file
from .utility import generate_csv, month_dict
import json
import pandas as pd
import csv
from django.http import FileResponse
from wsgiref.util import FileWrapper
import os
from django.core.mail import EmailMessage
from .Email import send_mail
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from rest_framework import serializers
from rest_framework.serializers import ValidationError


"""
User Data API
"""


@api_view(["GET"])
def user_profile(request, username):
    """
    List all events according to month and year
    """
    if request.method == "GET":
        user = User.objects.filter(username=username)
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


"""
Event Data API
"""


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @method_decorator(login_required)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save(creator=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    # @method_decorator(login_required)
    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop("partial", False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     print(serializer.validated_data)
    #     if serializer.validated_data["creator"] == request.user:  # to add .user.first_name
    #         self.perform_update(serializer)
    #         return Response(serializer.data)

    #     else:
    #         raise serializers.ValidationError(
    #             "You cannot edit the report you are not the creator"
    #         )


"""
Report API DATA
"""


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportWithEventSerializer

    @method_decorator(login_required)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        if serializer.validated_data["event"].creator == request.user:  # to add .user.first_name
            self.perform_create(serializer)
            return Response(serializer.data)

        else:
            raise serializers.ValidationError(
                "You cannot create the report you are not the creator"
            )

    # @method_decorator(login_required)
    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop("partial", False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     print(request.user)
    #     if serializer.validated_data["event"].creator == request.user:  # to add .user.first_name
    #         self.perform_update(serializer)
    #         return Response(serializer.data)

    #     else:
    #         raise serializers.ValidationError(
    #             "You cannot edit the report you are not the creator"
    #         )


"""
Image API DATA
"""


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        report_id = serializer.data["report"]
        report = Report.objects.get(pk=report_id)
        event = report.event
        serializer_context = {"request": request}
        report_json = ReportWithEventSerializer(report, context=serializer_context).data
        event_json = EventSerializer(event).data
        dates_len = len(event_json["dates"])
        filename = event_json["name"] + "$" + event_json["dates"][0]["start"][0:10]
        event_json["dates"] = {
            "start": event_json["dates"][0]["start"][0:10],
            "end": event_json["dates"][dates_len - 1]["end"][0:10],
        }
        for items in report_json["image"]:
            items["image"] = items["image"][22::]
        report_json["attendance"] = report_json["attendance"][22::]
        dept_list = []
        for items in event_json["departments"]:
            dept_list.append(items["department"])
        event_json["departments"] = dept_list
        print(event_json["departments"])

        report_json["event_data"]["organizer"] = report_json["event_data"]["organizer"].split(",") or report_json["event_data"]["organizer"].split(", ") or report_json["event_data"]["organizer"].split("\r\n")
        # print(report_json["event_data"])
        print(report_json["feedback_url"])
        params = {
            "report_dict": report_json,
            "event_dict": event_json,
            "request": request,
        }


        render_to_file("pdf.html", params, filename)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


# Here as soon as an image is added the json data of the report generated is taken for pdf generation
# All the function for pdf generation will be called in this create method
# Any update or new image addition will also override the previous csv or pdf generated

"""
Department API data
"""

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    @method_decorator(login_required)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        if serializer.validated_data["event"].creator == request.user:  # to add .user.first_name
            self.perform_create(serializer)
            return Response(serializer.data)

        else:
            raise serializers.ValidationError(
                "You cannot assign the department you are not the creator"
            )

    # @method_decorator(login_required)
    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop("partial", False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     print(serializer.validated_data)
    #     print(request.user)
    #     if serializer.validated_data["event"].creator == request.user:  # to add .user.first_name
    #         self.perform_update(serializer)
    #         return Response(serializer.data)

    #     else:
    #         raise serializers.ValidationError(
    #             "You cannot edit the departments you are not the creator"
    #         )


class DatesViewSet(viewsets.ModelViewSet):
    queryset = Dates.objects.all()
    serializer_class = DateSerializer

    @method_decorator(login_required)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        if serializer.validated_data["event"].creator == request.user:  # to add .user.first_name
            self.perform_create(serializer)
            return Response(serializer.data)
        else:
            raise serializers.ValidationError(
                "You cannot assign the dates you are not the creator"
            )

    # @method_decorator(login_required)
    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop("partial", False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     print(request.user)
    #     if serializer.validated_data["event"].creator_name == request.user:  # to add .user.first_name
    #         self.perform_update(serializer)
    #         return Response(serializer.data)
    #     else:
    #         raise serializers.ValidationError(
    #             "You cannot edit the dates you are not the creator"
    #         )

@api_view(["POST"])
def dates_multiple(request):
    list_dates = request.data
    for date in list_dates:
        print(date)
        x = DateSerializer(data=date)
        if x.is_valid():
            x.save()
        else:
            return HttpResponse(status=400)
    return HttpResponse('OK', status=200)

@api_view(["POST"])
def depts_multiple(request):
    list_depts = request.data
    for dept in list_depts:
        print(dept)
        x = DepartmentSerializer(data=dept)
        if x.is_valid():
            x.save()
        else:
            return HttpResponse(status=400)
    return HttpResponse('OK', status=200)


"""
Event data for calendar
"""
@api_view(["GET"])
def event_list_calendar_all(request):
    """
    List all events
    """
    if request.method == "GET":
        dates = Dates.objects.all()
        serializer = CalendarDateSerializer(dates, many=True)
        return Response(serializer.data)

"""
Event data by month
"""
@api_view(["GET"])
def event_list_by_month(request, month, year):
    """
    List all events according to month and year
    """
    if request.method == "GET":
        dates = Dates.objects.filter(start__month=month, start__year=year)
        serializer = CalendarDateSerializer(dates, many=True)
        return Response(serializer.data)

"""
Event data by date
"""
@api_view(["GET"])
def event_list_by_date(request, date):
    """
    List all Events according to date
    """
    if request.method == "GET":

        start_date = (datetime.strptime(date, '%Y-%m-%d') -timedelta(days = 1))
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days = 1))
        end_date = end_date.strftime('%Y-%m-%d')
        dates = Dates.objects.filter(start__date__range = [start_date,end_date]) #, end__date__lte = end_date)
        if not dates:
            dates = Dates.objects.filter(end__date__range = [start_date,end_date])
        events = set([d.event for d in dates.all()])
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

        # date_1 = Dates.objects.filter(start_date = date)
        # date_2 = Dates.objects.filter(end_date = date)
        # d3 = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days = 1))
        # d3 = d3.strftime('%Y-%m-%d')
        # d4 = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days = 1))
        # d4 = d4.strftime('%Y-%m-%d')
        # def date_return(obj):
        #     events = set([d.event for d in obj.all()])
        #     serializer = EventSerializer(events, many=True)
        #     return Response(serializer.data)
        #
        #
        # if date_1:
        #     if date_2:
        #         date_7 = date_1.union(date_2)
        #         date_return(date_7)
        #     date_return(date_1)
        #
        # elif date_2:
        #     date_return(date_2)
        #
        # else:
        #     while(true):
        #
        #         date_3 = Dates.objects.filter(end_date = d3)
        #         date_4 = Dates.objects.filter(start_date = d3)
        #
        #         if date_3 and date_4:
        #             date_return(date_3)
        #         elif date_3:
        #             date_return(date_3)
        #         elif date_4:
        #             raise serializers.ValidationError(
        #                 "Event DNE"
        #             )
        #
        #         date_5 = Dates.objects.filter(end_date = d4)
        #         date_6 = Dates.objects.filter(start_date = d4)
        #
        #         if date_5 and date_6:
        #             date_return(date_6)
        #         elif date_6:
        #             date_return(date_6)
        #         elif date_5:
        #             raise serializers.ValidationError(
        #                 "Event DNE"
        #             )
        #         d3 = (datetime.strptime(d3, '%Y-%m-%d') + timedelta(days = 1))
        #         d3 = d3.strftime('%Y-%m-%d')
        #         d4 = (datetime.strptime(d4, '%Y-%m-%d') - timedelta(days = 1))
        #         d4 = d4.strftime('%Y-%m-%d')


"""
Download PDF
"""


@api_view(["GET"])
def report_pdf_download(request, pk):
    if request.method == "GET":
        report = Report.objects.get(id=pk)
        event = report.event
        event_serializer = EventSerializer(event).data
        name = event_serializer["name"]
        date = event_serializer["dates"][0]["start"][0:10]
        response = HttpResponse(content_type="text/pdf")
        filename = "media/pdf/{}${}.pdf".format(name, date)
        download_name = "{}_Report.pdf".format(name)
        dataset = open(filename, "rb")
        response = HttpResponse(dataset, content_type="text/pdf")
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(
            download_name
        )
        return response


@api_view(["GET"])
def report_pdf_preview(request, pk):
    if request.method == "GET":
        report = Report.objects.get(id=pk)
        event = report.event
        event_serializer = EventSerializer(event).data
        name = event_serializer["name"]
        date = event_serializer["dates"][0]["start"][0:10]
        filename = "media/pdf/{}${}.pdf".format(name, date)
        dataset = open(filename, "rb")
        response = HttpResponse(dataset, content_type="application/pdf")
        return response


"""
Generate Month Report
"""


@api_view(["GET"])
def month_report(request, month, year):
    """
    List all events according to month and year
    """
    if request.method == "GET":
        event = Event.objects.filter(dates__start__month=month, dates__start__year=year)
        serializer = EventSerializer(event, many=True)
        serializer = list(serializer.data)
        li = []
        for item in serializer:
            print(item["id"])
            if item["id"] in li:
                serializer.remove(item)
            else:
                li.append(item["id"])
                item["dates"] = {
                    "start": item["dates"][0]["start"],
                    "end": item["dates"][len(item["dates"]) - 1]["end"],
                }
                dept_list = []
                for dept in item["departments"]:
                    dept = dept["department"]
                    dept_list.append(dept)
                item["departments"] = dept_list
                item["start"] = item["dates"]["start"][0:10]
                item["end"] = item["dates"]["end"][0:10]
                item.pop("dates")
        month_name = month_dict[month]
        filename = "media/csv_month/{}.csv".format(month_name)
        month_1 = [1,3,5,7,8,10,12]
        month_2 = [4,6,9,11]
        if month in month_1:
            start_date = "2019-{}-01".format(month)
            end_date = "2019-{}-31".format(month)  
        elif month in month_1:
            start_date = "2019-{}-01".format(month)
            end_date = "2019-{}-30".format(month)  
        else:
            start_date = "2019-{}-01".format(month)
            end_date = "2019-{}-28".format(month)  
        # start_date = "2019-{}-01".format(month)
        # end_date = "2019-{}-31".format(month)
        start_date = (datetime.strptime("2019-{}-01".format(month), '%Y-%m-%d'))
        end_date = (datetime.strptime("2019-{}-30".format(month), '%Y-%m-%d'))
        dates = pd.date_range(start_date, end_date)
        zf = pd.DataFrame(index=dates)
        df = pd.DataFrame.from_dict(serializer)
        df.to_csv(filename)
        nf = pd.read_csv(
            filename, index_col="start", parse_dates=True, na_values=["nan", "NaN"]
        )
        nf = nf.drop(columns=[nf.columns[0], nf.columns[1]])
        zf = zf.join(nf, how="inner")
        zf.to_csv(filename)
        dataset = open(filename, "r")
        response = HttpResponse(dataset, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="{}_Report.csv"'.format(
            month_name
        )
        return response


"""
Email PDF
"""


@api_view(["GET"])
@login_required()
def send_pdf(request, pk):
    if request.method == "GET":
        report = Report.objects.get(id=pk)
        event_obj = report.event
        name = report.event.name
        date = get_dates(event_obj)
        print(date)
        filename = "{}${}.pdf".format(name,date)
        response = HttpResponse(content_type="text/pdf")
        teacher_name = request.user.first_name + " " + request.user.last_name
        send_mail(filename, teacher_name, event_obj)
        return response


"""
User Signup
"""

class SignUp(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer


"""
User Activation
"""

def activate(request, uidb64, token):
    try:
        user = User.objects.get(pk=uidb64)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse("User Verification Successful")

    else:
        return HttpResponse("User verification failed")


# Model signal on_save -> PDF
# /report/pdf/1 -> Retrieve from MEDIA_URL
# /report/pdf/1/send_email -> Definitely send the Emails

@api_view(["GET"])
@login_required()
def get_event_list(request):
    if request.method == 'GET':
        user = User.objects.filter(id=request.user.id)
        event = Event.objects.filter(creator=user[0].id)
        serializer = EventSerializer(event, many=True)
        return Response(serializer.data)
