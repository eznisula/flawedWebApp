from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

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


def vote(request, question_id):

    '''
    POSSIBLE VULNERABILITY:
    https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/
    https://docs.djangoproject.com/en/4.2/intro/tutorial04/#id5
    
    The code for our vote() view does have a small problem. It 
    first gets the selected_choice object from the database, then 
    computes the new value of votes, and then saves it back to the 
    database. If two users of your website try to vote at exactly 
    the same time, this might go wrong: The same value, let’s say 
    42, will be retrieved for votes. Then, for both users the new 
    value of 43 is computed and saved, but 44 would be the 
    expected value.

    This is called a race condition. 
    If you are interested, you can read Avoiding race conditions 
    using F() to learn how you can solve this issue.

    '''

    question = get_object_or_404(Question, pk=question_id)
    try:
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
    