CREATE MIGRATION m1t6yoep6yyw6jkxkeykt57geutamhtzkrq5tl7simbfuxti4yowla
    ONTO m1l7fq2lttzvjjxazpop4ip6jyk54fspxkaf33rn6yxu22ylm2lslq
{
  CREATE TYPE default::Participant EXTENDING default::Auditable {
      CREATE REQUIRED LINK meeting: default::Meeting;
      CREATE REQUIRED PROPERTY name: std::str;
  };
  ALTER TYPE default::Meeting {
      CREATE MULTI LINK participants := (.<meeting[IS default::Participant]);
  };
  CREATE TYPE default::ParticipantDate EXTENDING default::Auditable {
      CREATE REQUIRED LINK participant: default::Participant {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE REQUIRED PROPERTY date: std::cal::local_date;
      CREATE CONSTRAINT std::exclusive ON ((.date, .participant));
      CREATE REQUIRED PROPERTY enabled: std::bool {
          SET default := true;
      };
      CREATE REQUIRED PROPERTY starrred: std::bool {
          SET default := false;
      };
  };
  ALTER TYPE default::Participant {
      CREATE MULTI LINK dates := (.<participant[IS default::ParticipantDate]);
  };
};
