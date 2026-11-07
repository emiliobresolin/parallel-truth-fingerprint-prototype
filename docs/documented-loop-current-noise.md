# Ruído de referência da corrente de malha

Correção do P14 autorizada em 29/10/2026. A perturbação uniforme `±(0,02 + 0,08r) mA`, dependente da demanda, foi identificada na auditoria como uma parametrização sem fonte instrumental independente. Sua substituição usa uma escala de ruído de saída medida em um circuito de referência para transmissores de corrente.

## Parâmetro publicado

**Texas Instruments, SLAAE91, março de 2023, _Ultra-Low-Power, Low-Voltage, 2-Wire, 4- to 20-mA Loop Transmitter Using AFE881H1_.** Na seção _Noise Performance_, tabela 1-2 da versão HTML, ou tabela 2, página 4 do PDF, o circuito baseado no AFE881H1 apresenta ruído RMS de **782 nA**. O ensaio utiliza corrente estática ajustada em 3 mA e ADC de 24 bits a 31 kSPS, com 16.383 amostras. A conversão de unidade é:

`782 nA = 0,782 µA = 0,000782 mA`.

[Fonte oficial HTML](https://www.ti.com/document-viewer/lit/html/slaae91), [PDF oficial](https://www.ti.com/lit/ab/slaae91/slaae91.pdf), [PDF arquivado](reference-archive/documents/TI_SLAAE91_2023_2_Wire_4_20mA_Transmitters.pdf).

Essa é a escala escolhida para o estágio elétrico genérico da emulação. Os nomes dos instrumentos continuam identificando referências funcionais de temperatura, pressão, rotação e vazão; o parâmetro de ruído é identificado separadamente como referência TI. O valor publicado corresponde ao circuito e à condição de medição acima. Sua aplicação constante no intervalo nominal é uma hipótese explícita do cenário, fixada antes da coleta.

## Método de geração

**Texas Instruments, SLVA043B, _Noise Analysis in Operational Amplifier Circuits_, 2007**, seção _Noise Characteristics_, página impressa 4, página 7 do PDF, apresenta o tratamento gaussiano do ruído e a igualdade entre desvio-padrão e RMS da componente de média zero. [PDF oficial](https://www.ti.com/lit/an/slva043b/slva043b.pdf), [cópia local](reference-archive/documents/TI_SLVA043B_2007_Noise_Analysis_Operational_Amplifier_Circuits.pdf).

**Analog Devices, _Activity: Noise_**, seção _Modeling and Measuring ADC noise_, versão aprovada em 06/09/2024, mostra a geração de amostras gaussianas com `random.normal` e a verificação pelo desvio-padrão. A orientação é usada como método computacional para uma componente de ruído amostrada. [Fonte oficial](https://wiki.analog.com/university/labs/noise_adalm2000), [HTML arquivado em 29/10/2026](reference-archive/documents/ADI_Activity_Noise_ADALM2000_2026-10-29.html).

Para cada canal `c` e aquisição `k`, a aproximação é:

```
z[c,k] ~ Normal(0, 1)
e[c,k] = 0,000782 mA × z[c,k]
I[c,k] = saturar_4_20(I_nominal[c,k] + bias[c] + e[c,k])
```

As amostras e os canais têm sequências pseudoaleatórias separadas e reproduzíveis por semente. A independência, a distribuição gaussiana e a extensão da escala RMS às diferentes correntes são escolhas do modelo amostrado. A TI fornece a escala medida; as referências de método sustentam a construção computacional. A taxa de 31 kSPS caracteriza a aquisição do ensaio de referência: ela não determina, por si só, a banda analógica equivalente ou um filtro para o nosso simulador. Por isso, o protocolo caracteriza RMS por amostra e registra o intervalo de aquisição, sem atribuir uma densidade espectral ou uma banda analógica medida ao modelo.

A saturação nominal de 4–20 mA é uma política explícita do cenário. Perto dos extremos ela altera a média e a variância da corrente resultante; a verificação de RMS usa correntes nominais no interior do intervalo e considera a componente antes da saturação. O multiplicador padrão é 1; o valor 0 permite controles sem ruído. Outros multiplicadores representam uma intervenção experimental declarada.

## Precisão e caminho da observação

A geração conserva a precisão numérica da corrente e retira a quantização global em passos de 0,001 mA. Esse passo era comparável ao RMS escolhido e modificaria a distribuição. As unidades de engenharia permanecem projeções para apresentação e envelope do transmissor. Consistência, comparação e entradas da LSTM continuam em mA.

O ruído é aplicado uma vez à observação adquirida. As réplicas e a supervisão normal recebem essa mesma observação; não são produzidas perturbações independentes para cada cópia digital. Assim, o critério de igualdade entre cópias da mesma origem continua coerente com a arquitetura.

## Evidência e nova execução

Os ensaios anteriores permanecem preservados como evidência da versão que os gerou. A versão corrigida exige nova coleta com o ruído documentado, seguida do treinamento, da calibração normal e da avaliação já definidos. O fluxo usa uma nova identificação de protocolo, semente de simulação 606 na confirmação com calibração comum e diretório próprio. Os parâmetros do detector e os ataques permanecem fixos; as taxas da nova versão serão calculadas a partir da execução.

As fontes arquivadas e seus SHA256 constam de `reference-archive/catalog/documented-loop-noise-sources.v1.json`. O teste técnico e a execução completa têm papéis separados: o primeiro verifica a cadeia; a segunda produz os resultados para a análise da tese.
