=============
django-cereal
=============

Efficient serialization of `Django`_ `Models`_ for use in `Celery`_ that ensure
the state of the world.

It supports Django 1.7, 1.8 and 1.9 for Python versions 2.7, 3.3, 3.4, 3.5 and
pypy (where Django supports the Python version).

.. _`Django`: https://www.djangoproject.com/
.. _`Models`: https://docs.djangoproject.com/en/stable/topics/db/models/
.. _`Celery`: http://www.celeryproject.org/

Scenario
========

If you're using `Django`_ and `Celery`_ you're most likely passing instances
of `models`_ back and forth between tasks or, as the Celery `docs suggest`_,
you're passing just the primary key to a task and then retrieving the the model
instance with the primary key.

If you're doing the former, it's potentially inefficient and certainly dangerous
as by the time the task executes the models data could be changed!

If you're using the later, you're probably wondering to yourself, surely there 
is a better way?! While it's efficient and certainly readable it's not exactly
much fun continually fetching the model at the start of each task...

You may also be using model methods as tasks, but unless you're using something
similar to `this refresh decorator`_, you'll potentially have stale model data.

django-cereal to the rescue...

.. _`Django`: https://www.djangoproject.com/
.. _`Celery`: http://www.celeryproject.org/
.. _`models`: https://docs.djangoproject.com/en/stable/topics/db/models/
.. _`docs suggest`: http://docs.celeryproject.org/en/latest/userguide/tasks.html?highlight=model#state
.. _`this refresh decorator`: https://bitbucket.org/alexhayes/django-toolkit/src/93d23b254bb1edcf31ff5b0f91673fc439f26438/django_toolkit/models/decorators.py?at=master#cl-3


How It Works
============

django-cereal works by using an alternative serializer before the task is sent
to the message bus and then retrieves a fresh instance of the model during
deserialization. Currently only `pickle`_ is supported (feel free to fork and
implement for JSON or YAML).

Essentially when the model is serialized only the primary key and the model's 
class are pickled. This is obviously not quite as efficient as pickling just the
models primary key, but it's certainly better than serializing the entire model!

When the task is picked up by a Celery worker and deserialized an instance of
the model is retrieved using :code:`YourModel.objects.get(pk=xxx)` and thus this
approach is also safe as you're not using stale model data in your task.

The serializer is `registered with kombu`_ and safely patches
:code:`django.db.Model.__reduce__` - it only operates inside the scope of kombu
and thus doesn't mess with a model's pickling outside of kombu.

.. _`pickle`: https://docs.python.org/2/library/pickle.html
.. _`registered with kombu`: http://kombu.readthedocs.org/en/latest/userguide/serialization.html#creating-extensions-using-setuptools-entry-points


Installation
============

You can install django-cereal either via the Python Package Index (PyPI)
or from github.

To install using pip;

.. code-block:: bash

    $ pip install django-cereal

From github;

.. code-block:: bash

    $ pip install git+https://github.com/alexhayes/django-cereal.git


Usage
=====

All that is required is that you specify the kwarg :code:`serializer` when
defining a task.

.. code-block:: python

    from django_cereal.pickle import DJANGO_CEREAL_PICKLE

    @app.task(serializer=DJANGO_CEREAL_PICKLE)
    def my_task(my_model):
        ...

There is also a helper task that you can use which defines the serializer if
it's not set.

.. code-block:: python

    from django_cereal.pickle import task

    @task
    def my_task(my_model):
        ...

Another approach is to set :code:`CELERY_TASK_SERIALIZER` to
:code:`django-cereal-pickle`.


Model Task Methods
==================

You can also use task methods on your Django models, so you don't have to define
them in a tasks.py. For example;

.. code-block:: python

    from celery.contrib.methods import task_method
    from django_cereal.pickle import DJANGO_CEREAL_PICKLE
    from yourproject.celery import app


    task_method_kwargs = dict(filter=task_method,
                          serializer=DJANGO_CEREAL_PICKLE)


    class MyModel(models.Model):

        @app.task(name='MyModel.foo', **task_method_kwargs)
        def foo(self):
            # self is an instance of MyModel


Then, you can call your task as follows;

.. code-block:: python

    bar = MyModel.objects.get(...)
    bar.foo.delay()


Just like your would a normal task but you can stop defining tasks that simply
orchestrate calls on a model and just call the model directly.


Chaining Task Methods
=====================

While not directly related to serialization of Django models, if you are using
Django Model methods as tasks, or any class methods as tasks for that matter,
and you are chaining these tasks you may be interested in the
`@ensure_self decorator`_ (see `Celery issue #2137`_ for more details).

.. _`@ensure_self decorator`: https://github.com/alexhayes/django-toolkit/blob/master/django_toolkit/celery/decorators.py#L3
.. _`Celery issue #2137`: https://github.com/celery/celery/issues/2137


Database Connections
====================

Note that if you use the :code:`--maxtasksperworker` flag in Celery, or under
other similar situations, the connection to a database in Django could become
unusable, with errors such as the following thrown;

.. code-block:: python

    OperationalError(2006, 'MySQL server has gone away')

This is now handled by the unpickling by closing down the database connection
which forces a new connection to be created.

Perhaps in the future there may be a nicer way of handling this, for instance,
a new connection is created each time a worker is created, but for now the fix
in place works, even if it's not ideal.


License
=======

This software is licensed under the `MIT License`. See the ``LICENSE``
file in the top distribution directory for the full license text.


Author
======

Alex Hayes <alex@alution.com>
