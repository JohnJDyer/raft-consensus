# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: raft.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='raft.proto',
  package='raft',
  syntax='proto3',
  serialized_pb=_b('\n\nraft.proto\x12\x04raft\"*\n\nRaftEntity\x12\x0b\n\x03pid\x18\x01 \x01(\x03\x12\x0f\n\x07ip_addr\x18\x02 \x01(\x0c\"+\n\nLogEntries\x12\x0c\n\x04term\x18\x01 \x01(\x03\x12\x0f\n\x07\x63ommand\x18\x02 \x01(\x0c\"\xca\x02\n\x0eRaftUDPMessage\x12:\n\x0cmessage_type\x18\x01 \x01(\x0e\x32$.raft.RaftUDPMessage.RaftMessageType\x12 \n\x06leader\x18\x02 \x01(\x0b\x32\x10.raft.RaftEntity\x12\x0c\n\x04term\x18\x03 \x01(\x03\x12 \n\x06sender\x18\x04 \x01(\x0b\x32\x10.raft.RaftEntity\x12\x12\n\ncommit_idx\x18\x05 \x01(\x03\x12\x0f\n\x07log_idx\x18\x06 \x01(\x03\x12\x0f\n\x07\x63ommand\x18\x07 \x01(\x0c\x12\x1d\n\x03log\x18\x08 \x03(\x0b\x32\x10.raft.LogEntries\"U\n\x0fRaftMessageType\x12\t\n\x05HEART\x10\x00\x12\x08\n\x04POLL\x10\x01\x12\x08\n\x04VOTE\x10\x02\x12\x0b\n\x07\x43OMMAND\x10\x03\x12\n\n\x06\x41PPEND\x10\x04\x12\n\n\x06STATUS\x10\x05\x62\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_RAFTUDPMESSAGE_RAFTMESSAGETYPE = _descriptor.EnumDescriptor(
  name='RaftMessageType',
  full_name='raft.RaftUDPMessage.RaftMessageType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='HEART', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='POLL', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='VOTE', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='COMMAND', index=3, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='APPEND', index=4, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='STATUS', index=5, number=5,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=355,
  serialized_end=440,
)
_sym_db.RegisterEnumDescriptor(_RAFTUDPMESSAGE_RAFTMESSAGETYPE)


_RAFTENTITY = _descriptor.Descriptor(
  name='RaftEntity',
  full_name='raft.RaftEntity',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='pid', full_name='raft.RaftEntity.pid', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='ip_addr', full_name='raft.RaftEntity.ip_addr', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=20,
  serialized_end=62,
)


_LOGENTRIES = _descriptor.Descriptor(
  name='LogEntries',
  full_name='raft.LogEntries',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='term', full_name='raft.LogEntries.term', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='command', full_name='raft.LogEntries.command', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=64,
  serialized_end=107,
)


_RAFTUDPMESSAGE = _descriptor.Descriptor(
  name='RaftUDPMessage',
  full_name='raft.RaftUDPMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='message_type', full_name='raft.RaftUDPMessage.message_type', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='leader', full_name='raft.RaftUDPMessage.leader', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='term', full_name='raft.RaftUDPMessage.term', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sender', full_name='raft.RaftUDPMessage.sender', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='commit_idx', full_name='raft.RaftUDPMessage.commit_idx', index=4,
      number=5, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='log_idx', full_name='raft.RaftUDPMessage.log_idx', index=5,
      number=6, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='command', full_name='raft.RaftUDPMessage.command', index=6,
      number=7, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='log', full_name='raft.RaftUDPMessage.log', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _RAFTUDPMESSAGE_RAFTMESSAGETYPE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=110,
  serialized_end=440,
)

_RAFTUDPMESSAGE.fields_by_name['message_type'].enum_type = _RAFTUDPMESSAGE_RAFTMESSAGETYPE
_RAFTUDPMESSAGE.fields_by_name['leader'].message_type = _RAFTENTITY
_RAFTUDPMESSAGE.fields_by_name['sender'].message_type = _RAFTENTITY
_RAFTUDPMESSAGE.fields_by_name['log'].message_type = _LOGENTRIES
_RAFTUDPMESSAGE_RAFTMESSAGETYPE.containing_type = _RAFTUDPMESSAGE
DESCRIPTOR.message_types_by_name['RaftEntity'] = _RAFTENTITY
DESCRIPTOR.message_types_by_name['LogEntries'] = _LOGENTRIES
DESCRIPTOR.message_types_by_name['RaftUDPMessage'] = _RAFTUDPMESSAGE

RaftEntity = _reflection.GeneratedProtocolMessageType('RaftEntity', (_message.Message,), dict(
  DESCRIPTOR = _RAFTENTITY,
  __module__ = 'raft_pb2'
  # @@protoc_insertion_point(class_scope:raft.RaftEntity)
  ))
_sym_db.RegisterMessage(RaftEntity)

LogEntries = _reflection.GeneratedProtocolMessageType('LogEntries', (_message.Message,), dict(
  DESCRIPTOR = _LOGENTRIES,
  __module__ = 'raft_pb2'
  # @@protoc_insertion_point(class_scope:raft.LogEntries)
  ))
_sym_db.RegisterMessage(LogEntries)

RaftUDPMessage = _reflection.GeneratedProtocolMessageType('RaftUDPMessage', (_message.Message,), dict(
  DESCRIPTOR = _RAFTUDPMESSAGE,
  __module__ = 'raft_pb2'
  # @@protoc_insertion_point(class_scope:raft.RaftUDPMessage)
  ))
_sym_db.RegisterMessage(RaftUDPMessage)


# @@protoc_insertion_point(module_scope)