from rest_framework.decorators import api_view
from rest_framework.decorators import action
from operator import itemgetter
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import jwt
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
import rest_framework_jwt

from api.api_permissions import OnlyAdminCanCreate


from api.models import User, Group, Agent, Event
from api.serializers import (
    UserModelSerializer,
    GroupModelSerializer,
    AgentModelSerializer,
    EventModelSerializer
)

# Create your views here.

class GroupApiViewSet(APIView):
    queryset = Group.objects.all()
    serializer_class = GroupModelSerializer

    def post(self, request, pk=None, format=None):
        serializer = GroupModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk=None, format=None):
        if not pk:
            groups = Group.objects.all()
            serializer = GroupModelSerializer(groups, many=True)
        else:
            group = Group.objects.get(pk=pk)
            serializer = GroupModelSerializer(group)

        return Response(serializer.data)


class UserApiViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer

class AgentApiViewSet(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = Agent.objects.all()
    serializer_class = AgentModelSerializer

    def post(self, request, pk=None, format=None):
        serializer = AgentModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # validation
        return self.list(request, *args, **kwargs)

class EventApiViewSet(mixins.ListModelMixin, generics.GenericAPIView):
    """authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminCanCreate]"""

    queryset = Event.objects.all()
    serializer_class = EventModelSerializer

    def post(self, request, pk=None, format=None):

        serializer = EventModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        """
        {"Enviroment": "Produção", "Order": "Level", "Buscar por":"Level", "Field": "critical"}
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        env = request.data.get('Enviroment')
        order = request.data.get('Order')
        search = request.data.get('Buscar por')
        field = request.data.get('Field')

        if not env:
            return self.list(request, *args, **kwargs)
        else:
            queryset = self.get_events_by_enviroment(env, search, field)
            if order == 'Level':
                return Response(data=queryset)
            elif order == 'Frequência':
                events_by_frequency = sorted(queryset, key=itemgetter("Eventos"), reverse=True)
                return  Response(data=events_by_frequency)

    def put(self, request, *args, **kwargs):
        """
        {"Enviroment": "Produção", "Level": "critical", "Data":"Ocorrencia1"}
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        env = request.data.get('Enviroment')
        level = request.data.get('Level')
        data = request.data.get('Data')

        queryset = Event.objects.filter(agent__env__contains=env,
                                        level__contains=level, data__contains=data).update(arquivado=True)

        if not queryset:
            return Response(f'Não existem eventos com os parametros informados')
        else:
            return Response(f'{queryset} eventos foram arquivados')

    def delete(self, request):
        """
              {"Enviroment": "Produção", "Level": "critical", "Data":"Ocorrencia1"}
              :param request:
              :param args:
              :param kwargs:
              :return:
              """
        env = request.data.get('Enviroment')
        level = request.data.get('Level')
        data = request.data.get('Data')

        queryset = Event.objects.filter(agent__env__contains=env,
                                        level__contains=level, data__contains=data)
        counter = 0

        if not queryset:
            return Response(f'Não existem eventos com os parametros informados')
        else:
            for events in queryset:
                events.delete()
                counter+=1
            return Response(f'{counter} eventos foram deletados')


    def get_events_by_enviroment(self, env, search, field):
        event_list = []

        if not search:
            queryset = Event.objects.filter(agent__env__contains=env).order_by('level')

        elif search == "Level":
            queryset = Event.objects.filter(agent__env__contains=env, level__contains=field).order_by('level')
        elif search == "Descrição":
            queryset = Event.objects.filter(agent__env__contains=env, data__contains=field).order_by('level')
        elif search == "Origem":
            queryset = Event.objects.filter(agent__env__contains=env, agent__address__contains=field).order_by('level')

        for events in queryset:
            level = events.level
            data = events.data
            date = events.date.strftime('%d-%m-%y %H:%M:%S')
            origem = events.agent.address
            event_dict = self.get_events_by_level_data(level, data, queryset, date, origem)

            if event_dict not in event_list:
                event_list.append(event_dict.copy())
            event_dict.clear()

        return event_list


    def get_events_by_level_data(self, level, data, database, date, origem):
        queryset = database.filter(level=level, data=data)
        queryset_count = database.filter(level=level, data=data).count()
        event_dict={}

        if queryset_count == 1:
            event_dict['Level'] = level
            event_dict['Log'] = {'Descrição': data, 'Origem do log': origem, 'Date': date}
            event_dict['Eventos'] = queryset_count
            return event_dict
        else:
            counter = 0
            for event in queryset:
                id = event.id
                if counter == 0:
                    first_log = id
                    event_dict['Level'] = event.level
                    event_dict['Log'] = {'Descrição': event.data,
                                         'Origem do log': event.agent.address,
                                         'Date': event.date.strftime('%d-%m-%y %H:%M:%S')
                                         }
                    event_dict['Eventos'] = queryset_count
                else:
                    if id <= first_log:
                        event_dict['Level'] = event.level
                        event_dict['Log'] = {'Descrição': event.data,
                                            'Origem do log': event.agent.address,
                                             'Date': event.date.strftime('%d-%m-%y %H:%M:%S')
                                             }
                        event_dict['Eventos'] = queryset_count
                        first_log = id
                counter+=1
        return event_dict


@api_view(["GET", "POST"])
def details(request):
            """
            {"Enviroment": "Desenvolvimento", "Level": "warning", "Data":"Ocorrencia3"}
            :param request:
            :return:
            """
            env = request.data.get('Enviroment')
            level = request.data.get('Level')
            data = request.data.get('Data')

            try:
                queryset = Event.objects.filter(agent__env__contains=env,
                                                level__contains=level, data__contains=data)
                detail = f'Erro no {queryset[0].agent.address} em {queryset[0].date.strftime("%d-%m-%y %H:%M:%S")}'
                title = queryset[0].data
                eventos = queryset.count()
                collected = queryset[0].user.name

                dicionario = {"Detalhes": detail, "Título": title, "Level": level, "Eventos": eventos,
                              "Coletado por": collected}

            except ValueError:

                dicionario = {"Enviroment": "Desenvolvimento", "Level": "critical", "Data": "Ocorrencia3"}
                return Response(f'informe algum parametro existente na base de dados para testar a função, exemplo:'
                                f'{dicionario}')

            return Response(dicionario)


@api_view(["POST", "GET"])
def cadastro(request):

    if request.method == "GET":
        exemplo={"name": "", "email": "", "password": ""}
        return Response(f'Digite seu nome, email e Senha ex: {exemplo}')

    else:

        name = request.data.get('name')
        password = request.data.get('password')
        email = request.data.get('email')
        payload = {'data': email}
        token = jwt.encode(payload, password, algorithm='HS256')

        queryset = User.objects.filter(email__contains=email)

        if queryset.count() == 0:
            user = User.objects.create(name=name, email=email, password=token)
            dicionario = {'status': 'Cadastrado com Sucesso',
                      'name': user.name, 'email': user.email, 'password': user.password}
            return Response(dicionario)
        else:
            return Response('Email consta em nossa base de dados')

@api_view(["GET", "POST"])
def login(request):

    """
    {
    "id": 2,
    "name": "ultimo",
    "email": "ultimo@gmail.com",
    "password": "12345678"
}
    :param request:
    :return:
    """
    if request.method == "GET":
        exemplo={"name": "", "email": "", "password": ""}
        return Response(f'Digite seu nome, email e Senha ex: {exemplo}')

    else:

        email = request.data.get('email')
        password = request.data.get('password')
        payload = {'data': email}
        token = jwt.encode(payload, password, algorithm='HS256')
        queryset = User.objects.filter(password__contains=token)

        if queryset:
            return Response({'Mensagem': f'Bem Vindo {queryset[0].name}', 'status': 'Senha Válida'})
        else:
            return Response('Senha Inválida')





















