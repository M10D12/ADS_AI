/* O Script usado para criar os models no backend  (criar a BD)*/

CREATE TABLE usuario (
	id		 BIGINT,
	nome		 BOOL NOT NULL,
	password_hash VARCHAR(512) NOT NULL,
	email	 VARCHAR(512),
	PRIMARY KEY(id)
);

CREATE TABLE filme (
	id	 BIGINT,
	nome	 VARCHAR(512) NOT NULL,
	descricao TEXT NOT NULL,
	rating	 FLOAT(8),
	PRIMARY KEY(id)
);

CREATE TABLE genero (
	nome	 VARCHAR(512),
	descricao TEXT NOT NULL,
	PRIMARY KEY(nome)
);

CREATE TABLE atividade_usuario (
	rating	 SMALLINT,
	visto	 BOOL DEFAULT false,
	favorito	 BOOL DEFAULT false,
	filme_id	 BIGINT NOT NULL,
	usuario_id BIGINT NOT NULL
);

CREATE TABLE filme_genero (
	filme_id	 BIGINT,
	genero_nome VARCHAR(512),
	PRIMARY KEY(filme_id,genero_nome)
);

ALTER TABLE atividade_usuario ADD CONSTRAINT atividade_usuario_fk1 FOREIGN KEY (filme_id) REFERENCES filme(id);
ALTER TABLE atividade_usuario ADD CONSTRAINT atividade_usuario_fk2 FOREIGN KEY (usuario_id) REFERENCES usuario(id);
ALTER TABLE filme_genero ADD CONSTRAINT filme_genero_fk1 FOREIGN KEY (filme_id) REFERENCES filme(id);
ALTER TABLE filme_genero ADD CONSTRAINT filme_genero_fk2 FOREIGN KEY (genero_nome) REFERENCES genero(nome);

