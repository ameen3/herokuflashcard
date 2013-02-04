from django.template import Context, loader, RequestContext
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from herokuflashcard.apps.flashcard.models import User, Cardset, Card, Session, VirtualCard, Temp_Card

import re
import hashlib
import random

SECRET = "secret"

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")



def cookie(request):
    request.set_cookie('username', 'baggnins')
    return render_to_response('cookie.html')


def home(request):
    if check_login(request):
        return HttpResponseRedirect('/welcome')
    return render_to_response('home.html', context_instance=RequestContext(request))


def login(request):
    if request.method == 'GET':
        if check_login(request):
            return HttpResponseRedirect('/welcome')
        return render_to_response('login.html', context_instance=RequestContext(request))

    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # check db for username
        try:
            user = User.objects.get(username__exact=username)
        except:
            user = None

        # username not found in db
        if not user:
            return render_to_response('login.html', {"username": username, "password": "",
                "error1": 'User not found', "error2": ""},
                context_instance=RequestContext(request))

        pass_hash = hash_str(password)
        # incorrect password
        if not pass_hash == user.password:
            return render_to_response('login.html', {"username": username, "password": "",
                "error1": "", "error2": "Password Incorrect"},
                context_instance=RequestContext(request))

        # authentication complete
        request.set_cookie('user_id', gen_cookie(username))
        return HttpResponseRedirect('/welcome')


def signup(request):
    if request.method == 'GET':
        if check_login(request):
            return HttpResponseRedirect('/welcome')
        return render_to_response('signup.html', context_instance=RequestContext(request))

    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        verify = request.POST.get('verify')
        # if proper signup
        if valid_username(username) and valid_password(password) and \
        valid_verify(password, verify) and new_username(username):
            pass_hash = hash_str(password)
            user = User(username=username, password=pass_hash)
            user.save()
            request.set_cookie('user_id', gen_cookie(username))
            return HttpResponseRedirect('/welcome')

        # if error(s)
        error1, error2, error3 = "", "", ""
        if not valid_username(username):
            error1 = "Please enter a valid username (3-20 alphanum chars)"
        elif not new_username(username):
            error1 = "Username is taken"
        if not valid_password(password):
            error2 = "Please enter a valid password (3-20 chars)"
        if not valid_verify(password, verify):
            error3 = "The passwords do not match"
        return render_to_response('signup.html',
            {'username': username, 'error1': error1, 'error2': error2,
            'error3': error3}, context_instance=RequestContext(request))


def welcome(request):
    user = get_user_from_cookie(request)
    if not user:
        return HttpResponseRedirect('/login')
    if request.method == 'GET':
        wipe_session(request, 'cardset', 'vcards', 'side', 'current_card')
        cardsets = Cardset.objects.filter(username=user.id)
        return render_to_response('welcome.html', {'username': user.username,
            'cardsets': cardsets}, context_instance=RequestContext(request))

    elif request.method == 'POST':
        edit = request.POST.get('edit')
        practice = request.POST.get('practice')

        if edit:
            cardset_title = edit
            cardsets = Cardset.objects.filter(username=user.id)
            cardset = cardsets.get(title__exact=cardset_title)
            request.session['cardset'] = cardset
            return HttpResponseRedirect('/edit')

        if practice:
            cardset_title = practice
            cardsets = Cardset.objects.filter(username=user.id)
            cardset = cardsets.get(title__exact=cardset_title)
            request.session['cardset'] = cardset
            return HttpResponseRedirect('/session_builder')


def create(request):
    user = get_user_from_cookie(request)
    if not user:
        return HttpResponseRedirect('/login')
    if request.method == 'GET':
        extra_cards = range(1, 11)
        return render_to_response('create.html', {'extra_cards': extra_cards,
            'tot_cards': 10},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        title = request.POST.get('title')
        tot_cards = int(request.POST.get('tot_cards'))
        if string_check(title) and new_cardset(title, user):
            create_cardset(request, title, user, tot_cards)
            return HttpResponseRedirect('/edit')

        elif not string_check(title):
            error = "Please enter a title"
            save = False
            cardset = None
            temp_cards, extra_cards, tot_cards = create_cards(request,
                                                tot_cards, cardset, save, user)
            return render_to_response('create.html',
                {'temp_cards': temp_cards, 'error': error,
                'extra_cards': extra_cards, 'tot_cards': tot_cards},
                context_instance=RequestContext(request))

        elif not new_cardset(title, user):
            error = "Cardset title is already in use"
            save = False
            cardset = None
            temp_cards, extra_cards, tot_cards = create_cards(request,
                                                tot_cards, cardset, save, user)
            return render_to_response('create.html',
                {'temp_cards': temp_cards, 'error': error, 'title': title,
                'extra_cards': extra_cards, 'tot_cards': tot_cards},
                context_instance=RequestContext(request))

        #need error messages, fix create.html template to accept a list of cards,
        #I want one create/edit template to do everything.  I have to
        #put some if statements in it so depending on whether I have a cardset
        #and cards it shows the cardset title at the top and displays the cards
        #I have to make ssure I allow 2 saves...after the initial save the user
        #will get a cardset title taken error...I should redirect to edit cardset
        #after 1st save to avoid that problem.  Edit should have a different view,
        #but work off the same template.  Solid.


def edit(request):
    #initialized with cardset model objects in session as 'cardset'
    user = get_user_from_cookie(request)
    if not user:
        return HttpResponseRedirect('/login')
    cardset = request.session.get('cardset')
        #check for a title change
    if request.method == 'GET':
        cards = Card.objects.filter(cardset__exact=cardset.id)
        cards = list(cards.order_by('number'))
        extra_cards, tot_cards = create_extra_cards(cards)
        return render_to_response('edit.html',
                {'cardset': cardset, 'cards': cards,
                'extra_cards': extra_cards, 'tot_cards': tot_cards},
                context_instance=RequestContext(request))

    elif request.method == 'POST':
        title = request.POST.get('title')
        tot_cards = int(request.POST.get('tot_cards'))
        if string_check(title):
            if title != cardset.title:
                if new_cardset(title, user):
                    cardset.title = title
                    error = ""
                    save = True
                else:
                    error = "A cardset with that title already exists"
                    save = False
            else:
                error = ""
                save = True

        elif not string_check(title):
            error = "Please enter a title"
            cardset = None
            save = False

        cards, extra_cards, tot_cards = create_cards(request, tot_cards,
                                        cardset, save, user)
        return render_to_response('edit.html', {'cards': cards,
            'extra_cards': extra_cards, 'tot_cards': tot_cards, 'error': error,
            'cardset': cardset}, context_instance=RequestContext(request))

def delete(request):
    cardset = request.session.get('cardset')
    cards = Card.objects.filter(cardset__exact=cardset.id)
    for card in cards:
        try:
            VirtualCard.objects.filter(card__exact=card.id).delete()
        except:
            pass
    try:
        cards.delete()
    except:
        pass
    cardset.delete()
    del request.session['cardset']
    return HttpResponseRedirect('/welcome')


def logout(request):
    request.delete_cookie('user_id')
    return HttpResponseRedirect('/login')


def session_namer(request):
    if request.method == 'GET':
        return render_to_response('session_namer.html',
                                  context_instance=RequestContext(request))

    elif request.method == 'POST':
        user = get_user_from_cookie(request)
        title = request.POST.get('title')
        if new_cardset(title, user) and new_session(title, user) and string_check(title):
            session = Session(username=user, title=title)
            session.save()
            new_vcards = request.session['new_vcards']
            vcards, cards_list = [], []
            count = 1
            for new_vcard in new_vcards:
                if new_vcard.card.id in cards_list:
                    continue
                else:
                    cards_list.append(new_vcard.card.id)
                    vcard = VirtualCard(number=count, card=new_vcard.card,
                                        session=session, state=1)
                    vcards.append(vcard)
                    vcard.save()
                    count += 1
            request.session['vcards'] = vcards
            session.num_cards = len(vcards)
            session.save()
            return HttpResponseRedirect('/practice')

        elif not string_check(title):
            error = "please enter a title"
            return render_to_response('session_namer.html', {'error': error},
                                  context_instance=RequestContext(request))

        else:
            error = "title is already taken"
            return render_to_response('session_namer.html', {'error': error},
                                  context_instance=RequestContext(request))


def session_builder(request):
    #comes from welcome with cardset model loaded in session
    #creates a list of vcard model objects for /practice
    #also creates and saves the session
    user = get_user_from_cookie(request)
    if not user:
        return HttpResponseRedirect('/login')
    cardset = request.session['cardset']
    session = Session(username=user, title=cardset.title)
    session.save()
    cards = list(Card.objects.filter(cardset__exact=cardset))
    vcards = []
    for card in cards:
        vcard = VirtualCard(number=card.number, card=card, session=session, state=1)
        vcard.save()
        vcards.append(vcard)
    session.num_cards = len(vcards)
    session.save()
    del(request.session['cardset'])
    request.session['vcards'] = vcards
    return HttpResponseRedirect('/practice')


def practice(request):
    #list of vcards is loaded in dj_session
    #session has been initialized
    user = get_user_from_cookie(request)
    if not user:
        return HttpResponseRedirect('/login')
    vcards = request.session['vcards']

    if request.method == 'GET':
        try:
            current_card = request.session['current_card']
        except:
            current_card = vcards[0]
        side = "q"
        request.session['side'] = side
        request.session['current_card'] = current_card
        return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))

    elif request.method == 'POST':
        # get stuff from session
        # get stuff from post
        # do stuff for each form input
        current_card = request.session['current_card']
        side = request.session['side']
        back, _next, answer, hint, question, wrong, correct, _exit, save, shuffle = practice_post_params(request)

        if back:
            try:
                current_card = vcards[current_card.number - 2]
            except:
                current_card = vcards[-1]
            side = "q"
            request.session['side'] = side
            request.session['current_card'] = current_card
            return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))

        elif _next:
            try:
                current_card = vcards[current_card.number]
            except:
                current_card = vcards[0]
            side = "q"
            request.session['side'] = side
            request.session['current_card'] = current_card
            return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))
        elif hint:
            side = "h"
            request.session['side'] = side
            return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))

        elif answer:
            side = "a"
            request.session['side'] = side
            return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))

        elif question:
            side = "q"
            request.session['side'] = side
            return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))

        elif wrong:
            vcards[current_card.number - 1].state = 0
            try:
                current_card = vcards[current_card.number]
            except:
                current_card = vcards[0]
            side = "q"
            request.session['side'] = side
            request.session['current_card'] = current_card
            request.session['vcards'] = vcards
            return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))

        elif correct:
            vcards[current_card.number - 1].state = 2
            try:
                current_card = vcards[current_card.number]
            except:
                current_card = vcards[0]
            side = "q"
            request.session['side'] = side
            request.session['current_card'] = current_card
            request.session['vcards'] = vcards
            return render_to_response('practice.html', {'vcard': current_card,
                           'side': side},
                           context_instance=RequestContext(request))

        elif _exit:
            return HttpResponseRedirect('/welcome')

        elif save:
            correct, wrong, skipped = 0, 0, 0
            for vcard in vcards:
                vcard.save()
                if vcard.state == 2:
                    correct += 1
                elif vcard.state == 1:
                    skipped += 1
                elif vcard.state == 0:
                    wrong += 1
            vcards[0].session.correct = correct
            vcards[0].session.wrong = wrong
            vcards[0].session.skipped = skipped
            vcards[0].session.save()
            return render_to_response('practice.html', {'vcard': current_card,
                      'side': side}, context_instance=RequestContext(request))

        elif shuffle:
            #shuffles only cards that haven't been answered yet
            shuffle_list = [vcard for vcard in vcards if vcard.state == 1]
            unshuffled = [vcard for vcard in vcards if vcard.state != 1]
            random.shuffle(shuffle_list)
            vcards = unshuffled + shuffle_list
            for i in range(len(vcards)):
                vcards[i].number = i + 1
            current_card = vcards[len(unshuffled)]

            side = "q"
            request.session['side'] = side
            request.session['current_card'] = current_card
            request.session['vcards'] = vcards
            return render_to_response('practice.html', {'vcard': current_card,
                      'side': side}, context_instance=RequestContext(request))

def stats(request):
    user = get_user_from_cookie(request)
    if not user:
        return HttpResponseRedirect('/login')
    sessions = Session.objects.filter(username__exact=user).order_by('-created')


    if request.method == 'GET':
        for session in sessions:
            if null_session(session):
                session.delete()
        sessions = Session.objects.filter(username__exact=user).order_by('-created')
        return render_to_response('stats.html', {'sessions': sessions,
                                  'username': user.username},
                                  context_instance=RequestContext(request))

    elif request.method == 'POST':
        delete_list = request.POST.getlist('delete')
        if delete_list:
            delete_sessions(sessions, delete_list)
            sessions = Session.objects.filter(username__exact=user).order_by('-created')
            return render_to_response('stats.html', {'sessions': sessions,
                                  'username': user.username},
                                  context_instance=RequestContext(request))
        study_list = request.POST.getlist('study')
        #creates a filtered list of vcards, stores it in session, and goes to
        #session namer
        if study_list:
            pos_vcards = []
            for session in sessions:
                for study in study_list:
                    if session.id == int(study):
                        pos_vcards = pos_vcards + list(VirtualCard.objects.filter(session__exact=session))

            selection = request.POST.getlist('selection')
            new_vcards = []
            if selection:
                #new_vcards = [pos_vcard for pos_vcard in pos_vcards for choice in selection if int(choice) == pos_vcard.state]
                for pos_vcard in pos_vcards:
                    for choice in selection:
                        if int(choice) == pos_vcard.state:
                            new_vcards.append(pos_vcard)

            if new_vcards is None or new_vcards == []:
                error = "study selection has no cards"
                return render_to_response('stats.html', {'sessions': sessions,
                                  'username': user.username, 'error': error},
                                  context_instance=RequestContext(request))
            request.session['new_vcards'] = new_vcards
            return HttpResponseRedirect('/session_namer')
        else:
            return render_to_response('stats.html', {'sessions': sessions,
                                  'username': user.username},
                                  context_instance=RequestContext(request))





"""----------------------------------------------------------------------------
Non-view functions"""


def gen_cookie(username):
    try:
        str(username)
    except:
        pass
    hash_id = hash_str(username)
    return username + "|" + hash_id


def check_login(request):
    #redirects to welcome if a valid cookie is present
    user_id = request.COOKIES.get('user_id')
    if user_id:
        try:
            user = User.objects.get(username__exact=user_id.split('|')[0])
        except:
            return False
        return check_user_id(user_id)


def check_user_id(user_id):
    user_id_hash = user_id.split('|')[1]
    return hash_str(user_id.split('|')[0]) == user_id_hash


def hash_str(s):
    return hashlib.md5(SECRET + s).hexdigest()


def new_username(username):
    #returns True if username isn't taken
    try:
        user = User.objects.get(username__exact=username)
    except:
        return True
    return False


def valid_verify(password, verify):
    return password == verify


def valid_username(username):
    return USER_RE.match(username)


def valid_password(password):
    return PASS_RE.match(password)


def get_user_from_cookie(request):
    #validates login via cookie
    #returns user object
    user_id = request.COOKIES.get('user_id')
    if user_id:
        if check_user_id(user_id):
            username = user_id.split('|')[0]
        try:
            user = User.objects.get(username__exact=username)
        except:
            return False
        return user
    else:
        return False


def wipe_session(request, *args):
    for arg in args:
        try:
            del request.session[arg]
        except:
            pass


def string_check(*args):
    for arg in args:
        if arg == " " or arg == "":
            return False
    return True


def new_cardset(title, user):
    #returns True if cardset isn't taken for username
    try:
        cardsets = Cardset.objects.filter(username__exact=user.id)
        cardset = cardsets.get(title__exact=title)
        return False
    except:
        return True


def new_session(title, user):
    sessions = Session.objects.filter(username__exact=user)
    try:
        session = sessions.get(title__exact=title)
        return False
    except:
        return True


def create_cardset(request, title, user, tot_cards):
    #saves the cardset and cards to the database
    #also saves the cardset to the session, to be passed to /edit
    cardset = Cardset(title=title, username=user)
    request.session['cardset'] = cardset
    cardset.save()
    count = 1
    for i in range(1, tot_cards + 1):
        q, a, h = get_card(request, i)
        if string_check(q, a):
            card = Card(number=count, question=q, answer=a, hint=h,
                        cardset=cardset)
            card.save()
            count += 1


def create_cards(request, tot_cards, cardset, save, user):
    #creates a list of card model objects, a list of extra cards
    #and keeps track of the total number of cards
    #Also adds extra_cards to the total number as needed
    #if save is true, saves the cardset and the cards (deletes former cards)
    # returns the cards, blank extra_cards, and tot_cards
    if save:
        request.session['cardset'] = cardset
        cardset.save()
        Card.objects.filter(cardset__exact=cardset.id).delete()
    cards = []
    if not tot_cards:
        tot_cards = 10
    count = 1
    for i in range(1, tot_cards + 1):
        q, a, h = get_card(request, i)
        if string_check(q, a):
            if save:
                card = Card(number=count, question=q, answer=a, hint=h,
                            cardset=cardset)
                card.save()
            else:
                card = Temp_Card(number=count, question=q, answer=a, hint=h)
            cards.append(card)
            count += 1
    cards = delete_cards(request, cards, save)
    add = add_cards(request)
    extra_cards, tot_cards = create_extra_cards(cards, tot_cards, add)
    return cards, extra_cards, tot_cards


def create_extra_cards(cards, tot_cards=0, add=0):
#based on the number of cards, creates extra blank cards, and tot_cards
    try:
    # will raise an exception if no cards are entered
        if not tot_cards:
            tot_cards = cards[-1].number
        if tot_cards <= 10:
            tot_cards = 10
        tot_cards += add
        add = 0  # if exception is raised on next line, add wont be added twice
        extra_cards = range(cards[-1].number + 1, tot_cards + 1)
    except IndexError:
    # if no cards, will generate extra cards based on total cards
        if tot_cards <= 10:
            tot_cards = 10
        tot_cards += add
        extra_cards = range(1, tot_cards + 1)
    return extra_cards, tot_cards


def delete_cards(request, cards, save):
#deletes cards if their boxes were checked
#then re-numbers the remaining cards
    delete = request.POST.getlist('delete')
    for e in delete:
        index = 0
        for card in cards:
            if int(e) == card.number:
                card.delete()
                del cards[index]
            index += 1
    count = 1
    for card in cards:
        card.number = count
        count += 1
        if save:
            card.save()
    return cards


def delete_sessions(sessions, delete_list):
    for e in delete_list:
        for session in sessions:
            if int(e) == session.id:
                session.delete()
                del(session)

def null_session(session):
    if session.correct == 0 and session.wrong == 0 and session.skipped == 0:
        return True
    else:
        return False


def get_card(request, i):
    #gets card attributes from request
    q = request.POST.get('q%d' % i)
    a = request.POST.get('a%d' % i)
    h = request.POST.get('h%d' % i)
    return q, a, h


def add_cards(request):
    add = request.POST.get('add')
    try:
        add = int(add)
    except:
        add = 0
    return add

def practice_post_params(request):
    back = request.POST.get('back')
    _next = request.POST.get('next')
    answer = request.POST.get('answer')
    hint = request.POST.get('hint')
    question = request.POST.get('question')
    wrong = request.POST.get('wrong')
    correct = request.POST.get('correct')
    _exit = request.POST.get('exit')
    save = request.POST.get('save')
    shuffle = request.POST.get('shuffle')
    return back, _next, answer, hint, question, wrong, correct, _exit, save, shuffle
