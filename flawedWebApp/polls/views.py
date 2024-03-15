from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.conf import settings
from django.db.models import F
from django.db import connection
from django.views.decorators.csrf import csrf_exempt

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        # Return the last five published questions (not including those set
        # to be published in the future).
        
        return Question.objects.filter(
            pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        # Excludes any questions that aren't published yet.
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


# Comment/uncomment this and set settings.FIX_CSRF_CHECK = True to test flaw
#@csrf_exempt
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        other = request.POST["other"]
        if other:
            if settings.FIX_SQL_INJECTION:
                # Safe way of dealing with the "other" SQL input
                selected_choice = question.choice_set.create(choice_text=other)
            else:
                # This is the dangerous way
                with connection.cursor() as cursor:
                    cursor.executescript(
                        "INSERT INTO polls_choice (choice_text, votes, question_id) \
                              VALUES ('{}', '0', '{}')".format(other, question.id))
                selected_choice = question.choice_set.get(choice_text=other)
        else:
            selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        if settings.FIX_VOTE_RACE_CONDITION:
            selected_choice.votes = F("votes") + 1            
        else:
            selected_choice.votes += 1

        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.

        '''
        POSSIBLE VULNERABILITY:
        Not redirecting after dealing with POST data?
        '''

        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
    