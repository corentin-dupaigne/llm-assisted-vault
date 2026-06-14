---
difficulty: medium
neetcode_section: Arrays & Hashing
struggled: true
project: neetcode-150
date_solved: 2026-06-13
review_after: 2026-06-20
reviews: 0
tags:
  - leetcode
  - neetcode-150
  - arrays-hashing
---
## Initial Intuition

Mon intuition est qu'il faut ajouter un ou plusieurs caracteres delimiteurs entre chaque mot pour encode. Puis dans la fonction decode en iterant sur les byte du string on append chaque byte dans une variable out of the scope (current_word) et des qu'on croise le caractere delimiteur on append le mot forme dans le array et on vide la variable current_word. Le souci est qu'il faut s'assurer que la variable delimiteur n'entre pas en conflit avec les bytes des mots, il faut donc s'assurer de trouver un delimiteur qui ne sera pas conflictuel. Theoriquement il serait possible d'avoir un string long de caracteres aleatoires comme delimiteur et il sera tres peu probable que les string fournis contiennent ce string exact mais cela n'est pas optimal.
Je pense qu'il faudrait utiliser un delimiteur dynamique, par exemple la longueur du string. Ou bien on pourrait ajouter au debut du string encode la longueur de chaque mot separee par un delimiteur (le delimiteur est necessaire pour eviter les bug dans le cas ou des mots ont des longueurs depassant les chiffres). Puis en decodant il faudra simplement garder en memoire la longueur de chaque mots puis former les mots en iterant jusqu'a longueur_mot[i]. Il faut egalement gerer le conflit potentiel entre le delimiteur et le contenu des strings. Par exemple si j'append 8%4%3%. Il faut ecrire dans le texte append au debut du string la longueur du string contenant les metadata donnant la longueur de chaque mot.
-> 83%4%6%8% // 9 est le nombre de caracteres apres lui meme, de ce fait la fonction de decoding sait ou les metadata s'arretent.


## My Solution

```go
type Solution struct{}

func (s *Solution) Encode(strs []string) string {
	if len(strs) == 1 && strs[0] == "" {
		return ""
	}

	var res strings.Builder
	var length_words []int
	for _, word := range strs {
		length_words = append(length_words, len(word))
		res.WriteString(word)
	}

	var b strings.Builder
	for _, length := range length_words {
		b.WriteString(strconv.Itoa(length))
		b.WriteRune('%')
	}

	metadata := strconv.Itoa(len(b.String())) + "%" + b.String()

	fmt.Println(metadata + res.String())

	return metadata + res.String()

}

func (s *Solution) Decode(encoded string) []string {

	if len(encoded) == 0 {
		return []string{""}
	}

	var length_metadata int
	var start_index int

	var buf []byte
	for i, r := range encoded {
		if r == '%' {
			length_metadata, _ = strconv.Atoi(string(buf))
			start_index = i + 1
			break
		} else {
			// buf += encoded[i]
			buf = append(buf, encoded[i])
		}
	}

	var res []string

	metadata_end := start_index + length_metadata
	i := start_index                   // start of metatadata after metadata length
	j := start_index + length_metadata // start of encoded string

	var buf2 []byte
	for i < metadata_end {
		if encoded[i] == '%' {
			i++
			length, _ := strconv.Atoi(string(buf2))
			
			buf2 = buf2[:0]
			b := 0
			for b = j; b < j+length; b++ {
				buf2 = append(buf2, encoded[b])
			}
			j = b
			res = append(res, string(buf2))
			buf2 = buf2[:0]
		} else {
			// buf2 += encoded[i]
			buf2 = append(buf2, encoded[i])
			i++
		}

	}

	fmt.Println(res)

	return res
}




// Time: O(n)
// Space: O(n + k)

```

### Optimal Solution

```go
type Solution struct{}

func (s Solution) Encode(strs []string) string {
    res := ""
    for _, str := range strs {
        res += strconv.Itoa(len(str)) + "#"
        res += str
    }

    return res
}

func (sSolution) Decode(encoded string) []string {
    result := []string{}
    i := 0
    for i < len(encoded) {
        j := i
        for encoded[j] != '#' {
            j++
        }
        length, _ := strconv.Atoi(encoded[i:j])
        result = append(result, encoded[j+1:j+1+length])
        i = j + 1 + length
    }
    return result
}

// Time: O(n)
// Space: O(1)

```

## Delta

Ma solution est optimale en terme de temps mais pas en terme de stockage. 


## Pattern

<!-- "When I see X, I think Y." — phrased generically -->


## Review Log

<!-- Date — could you reproduce it cold? what tripped you up? -->
- 2026-06-13 — first solve
