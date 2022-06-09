import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice


def create_question(question_text, days):
    """Create a question with the given 'question_text' and published the given number of 'days' offset to now (
    negative for question published in the past, positive for question that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


def create_choices_for_question(question, *choices: Choice):
    for choice in choices:
        question.choice_set.create(choice_text=choice.choice_text, votes=choice.votes)

    return question.choice_set.all()


class QuestionDetailViewTest(TestCase):
    def test_question_with_choices(self):
        """If a question exist and has choices will display the details about the question"""
        question = create_question("is test?", days=0)

        choice1 = Choice(question, choice_text="yes sir", votes=0)
        choice2 = Choice(question, choice_text="yes sir", votes=0)
        choice3 = Choice(question, choice_text="yes sir", votes=0)

        result = create_choices_for_question(question, choice1, choice2, choice3)
        expected = Choice.objects.filter(question__pk=question.pk)

        response = self.client.get(reverse('polls:detail', kwargs={'pk': question.pk}))

        self.assertEquals(response.status_code, 200)

        self.assertEqual(response.context['question'], question)
        self.assertQuerysetEqual(list(result), list(expected))


class QuestionIndexViewTest(TestCase):
    def test_no_question(self):
        """If no question exist, an appropriate message is displayed
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """Question with  a pub_date in the past are displayed on the index page"""

        question = create_question(question_text='Past Question', days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question]
        )

    def test_future_question(self):
        """Question with a pub_date in the futre aren't displayed on the index page"""
        question = create_question(question_text='Past Question', days=30)
        response = self.client.get(reverse('polls:index'))

        self.assertContains(response, "No polls are available.")

        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            []
        )

    def test_past_and_future_question(self):
        """Even if both past and future question exist, only past question are displayed"""
        question = create_question(question_text="Past question", days=-30)

        # new model with future publication date
        create_question(question_text="Future question", days=30)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question]
        )

    def test_two_past_question(self):
        """The question index page may display multiple questions"""
        # Creating mocks models to validate later
        question1 = create_question(question_text="Past Question 1", days=-29)
        question2 = create_question(question_text="Past Question 2", days=-3)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question2, question1]
        )


class QuestionModelTest(TestCase):

    def test_was_published_recently_with_future_question(self):
        """was_published_recently() returns False for questions whose pub_date is in the future."""

        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)

        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """was_published_recently() returns False for question whose pub_date is older than 1 day"""
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        mock_old_question = Question(pub_date=time)

        self.assertIs(mock_old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """was_published_recently() returns Trues for question whose pub_date is whithin the last days"""
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        mock_recent_question = Question(pub_date=time)

        self.assertIs(mock_recent_question.was_published_recently(), True)
