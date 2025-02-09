.. meta::
   :title: Documentation - Acord [Models]
   :type: website
   :url: https://acord.readthedocs.io/api/models.html
   :description: All the models created to simplify interactions with the discord API
   :theme-color: #f54646

.. currentmodule:: acord

******
Models
******
Our models use the ``Pydantic`` module for simple data parsing. 
All methods from :class:`~pydantic.BaseModel` are inherited along with ours.
These methods will not be shown in our docs, you can find them in ``Pydantic``'s documentation.

Emoji
~~~~~

.. attributetable:: Emoji

.. autoclass:: Emoji
   :members:

Guild
~~~~~

.. attributetable:: Guild

.. autoclass:: Guild
   :members:

Message
~~~~~~~

.. attributetable:: Message

.. autoclass:: Message
   :members:

TextChannel
~~~~~~~~~~~

.. attributetable:: TextChannel

.. autoclass:: TextChannel
   :members:

User
~~~~

.. attributetable:: User

.. autoclass:: User
   :members:
